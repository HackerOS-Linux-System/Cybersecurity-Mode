use anyhow::Result;
use smithay::reexports::calloop::EventLoop;
use tracing::{info, warn};
use crate::state::CmState;

pub fn init(state: &mut CmState, event_loop: &mut EventLoop<'static, CmState>) -> Result<()> {
    let use_drm = std::env::var("DISPLAY").is_err()
        && std::env::var("WAYLAND_DISPLAY")
               .map(|v| !v.contains("cm-"))
               .unwrap_or(true);

    if use_drm {
        info!("Using DRM/KMS backend (TTY)");
        match init_drm(state, event_loop) {
            Ok(_)  => return Ok(()),
            Err(e) => warn!("DRM init failed ({}), falling back to winit", e),
        }
    }

    info!("Using winit backend");
    init_winit(state, event_loop)
}

// ── DRM ───────────────────────────────────────────────────────────────────

fn init_drm(state: &mut CmState, event_loop: &mut EventLoop<'static, CmState>) -> Result<()> {
    use smithay::{
        backend::{
            libinput::{LibinputInputBackend, LibinputSessionInterface},
            renderer::gles::GlesRenderer,
            session::{libseat::LibSeatSession, Session},
            udev::{UdevBackend, UdevEvent},
        },
        output::{Mode as OutputMode, Output, PhysicalProperties, Subpixel},
        utils::Transform,
    };

    let (session, _notifier) = LibSeatSession::new()
        .map_err(|e| anyhow::anyhow!("libseat: {}", e))?;
    let seat_name = session.seat();
    info!("libseat session: {}", seat_name);

    let udev = UdevBackend::new(&seat_name)
        .map_err(|e| anyhow::anyhow!("udev: {}", e))?;

    let lh = event_loop.handle();

    lh.insert_source(udev, |event, _, st| {
        match event {
            UdevEvent::Added { device_id, path } => {
                tracing::info!("DRM device hotplugged: {:?}", path);
                // Re-enumerate outputs for newly connected monitor
                // In full impl: open DRM node, detect connectors, call add_output()
                // For now: notify via IPC
                if let Some(tx) = &st.ipc_tx {
                    tx.send(crate::ipc_bridge::CompositorEvent::OutputHotplugged {
                        name: format!("{:?}", path),
                        width: 1920, height: 1080, refresh: 60,
                        connected: true,
                    }).ok();
                }
            }
            UdevEvent::Removed { device_id, path } => {
                tracing::info!("DRM device removed: {:?}", path);
                if let Some(tx) = &st.ipc_tx {
                    tx.send(crate::ipc_bridge::CompositorEvent::OutputHotplugged {
                        name: format!("{:?}", path),
                        width: 0, height: 0, refresh: 0,
                        connected: false,
                    }).ok();
                }
            }
            _ => {}
        }
    }).map_err(|e| anyhow::anyhow!("udev source: {}", e))?;

    // Libinput for keyboard/mouse/touchpad
    let mut libinput_ctx = input::Libinput::new_with_udev(
        LibinputSessionInterface::from(session.clone())
    );
    libinput_ctx.udev_assign_seat(&seat_name).ok();

    let libinput_backend = LibinputInputBackend::new(libinput_ctx);
    lh.insert_source(libinput_backend, |event, _, st| {
        crate::input::process_input_event(st, event);
    }).map_err(|e| anyhow::anyhow!("libinput: {}", e))?;

    add_output(state, "DRM-1", 1920, 1080, 60);
    info!("DRM backend initialized");
    Ok(())
}

// ── Winit (smithay 0.7) ───────────────────────────────────────────────────

fn init_winit(state: &mut CmState, event_loop: &mut EventLoop<'static, CmState>) -> Result<()> {
    use smithay::{
        backend::{
            renderer::gles::GlesRenderer,
            winit::{self, WinitEvent},
        },
        output::{Mode as OutputMode, Output, PhysicalProperties, Subpixel},
        utils::Transform,
    };

    // smithay 0.7: winit::init::<GlesRenderer>() -> (WinitGraphicsBackend, WinitEventLoop)
    let (mut backend, winit_evt_loop) = winit::init::<GlesRenderer>()
        .map_err(|e| anyhow::anyhow!("winit: {:?}", e))?;

    let size = backend.window_size();
    let (w, h) = (size.w, size.h);
    info!("Winit window: {}x{}", w, h);

    add_output(state, "winit", w as i32, h as i32, 60);

    // smithay 0.7: WinitGraphicsBackend must be moved into closure
    // Use a shared mutex approach
    use std::sync::{Arc, Mutex};
    let backend_arc = Arc::new(Mutex::new(backend));

    event_loop.handle()
        .insert_source(winit_evt_loop, move |event, _, st| {
            match event {
                WinitEvent::Resized { size, .. } => {
                    st.output_size = (size.w as i32, size.h as i32).into();
                }
                WinitEvent::Input(ev) => {
                    crate::input::process_input_event(st, ev);
                }
                WinitEvent::CloseRequested => {
                    st.exit();
                }
                WinitEvent::Redraw => {
                    if let Ok(mut b) = backend_arc.lock() {
                        crate::render::render_frame(st, &mut b);
                    }
                }
                WinitEvent::Focus(_) => {}
                _ => {}
            }
        })
        .map_err(|e| anyhow::anyhow!("winit source: {}", e))?;

    info!("Winit backend initialized: {}x{}", w, h);
    Ok(())
}

// ── Shared output creation ─────────────────────────────────────────────────

fn add_output(state: &mut CmState, name: &str, w: i32, h: i32, refresh_hz: i32) {
    use smithay::{
        output::{Mode as OutputMode, Output, PhysicalProperties, Subpixel},
        utils::Transform,
    };

    let output = Output::new(
        name.to_string(),
        PhysicalProperties {
            size:     (w as u32 * 10 / 38, h as u32 * 10 / 38).into(),
            subpixel: Subpixel::Unknown,
            make:     "CM".into(),
            model:    "Display".into(),
        },
    );

    let mode = OutputMode { size: (w, h).into(), refresh: refresh_hz * 1000 };
    output.change_current_state(
        Some(mode), Some(Transform::Normal), None, Some((0, 0).into()),
    );
    output.set_preferred(mode);

    state.space.map_output(&output, (0, 0));
    state.output_size = (w, h).into();
    info!("Output: {} {}x{}@{}Hz", name, w, h, refresh_hz);
}
