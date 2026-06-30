use serde_json;
// compositor/src/main.rs — CM Compositor entry point

mod backend;
mod ipc_bridge;
mod handlers;
mod input;
mod protocols;
mod render;
mod state;
mod xwayland;

use anyhow::Result;
use smithay::reexports::{
    calloop::EventLoop,
    wayland_server::Display,
};
use state::{CmState, CompositorMode};
use tracing::info;

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            std::env::var("CM_LOG")
                .unwrap_or_else(|_| "info".into())
        )
        .init();

    let mode_str = std::env::args().nth(1).unwrap_or_else(|| "environment".into());
    let mode = match mode_str.as_str() {
        "mode" => CompositorMode::Mode,
        _      => CompositorMode::Environment,
    };

    info!("CM Compositor v0.2 — mode: {:?}", mode);
    run(mode)
}

pub fn run(mode: CompositorMode) -> Result<()> {
    let mut event_loop: EventLoop<CmState> = EventLoop::try_new()
        .map_err(|e| anyhow::anyhow!("EventLoop: {}", e))?;

    let mut display: Display<CmState> = Display::new()
        .map_err(|e| anyhow::anyhow!("Display: {}", e))?;

    let socket_name = std::env::var("WAYLAND_DISPLAY")
        .unwrap_or_else(|_| format!("wayland-cm-{}", match mode {
            CompositorMode::Environment => "environment",
            CompositorMode::Mode        => "mode",
        }));

    let mut state = CmState::new(&mut event_loop, &mut display, mode, socket_name.clone())?;

    // Insert display into event loop
    {
        let display_handle = display.handle();
        event_loop
            .handle()
            .insert_source(
                smithay::reexports::calloop::generic::Generic::new(
                    display,
                    smithay::reexports::calloop::Interest::READ,
                    smithay::reexports::calloop::Mode::Level,
                ),
                |_, display_ref, state| {
                    unsafe { display_ref.get_mut().dispatch_clients(state)? };
                    Ok(smithay::reexports::calloop::PostAction::Continue)
                },
            )
            .map_err(|e| anyhow::anyhow!("Display source: {}", e))?;
    }

    // Init backend (DRM or winit)
    backend::init(&mut state, &mut event_loop)?;

    // Init XWayland
    if state.config.enable_xwayland {
        if let Err(e) = xwayland::init(&mut state) {
            tracing::warn!("XWayland: {}", e);
        }
    }

    // Set up IPC bridge: compositor events → CM shell via /tmp/cm-ipc.sock
    {
        let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel::<ipc_bridge::CompositorEvent>();
        state.ipc_tx = Some(tx);

        // Forward compositor events to CM IPC server
        let rt = tokio::runtime::Handle::try_current();
        if let Ok(handle) = rt {
            handle.spawn(async move {
                let ipc_path = "/tmp/cm-ipc.sock";
                loop {
                    while let Ok(event) = rx.try_recv() {
                        if let Ok(mut stream) = tokio::net::UnixStream::connect(ipc_path).await {
                            use tokio::io::AsyncWriteExt;
                            let method = match &event {
                                ipc_bridge::CompositorEvent::WindowAdded { id, title, app_id } =>
                                    format!(r#"{{"method":"event.window_added","params":{{"id":{},"title":{},"app_id":{}}}}}"#,
                                        id, serde_json::to_string(title).unwrap_or_default(),
                                        serde_json::to_string(app_id).unwrap_or_default()),
                                ipc_bridge::CompositorEvent::WindowRemoved { id } =>
                                    format!(r#"{{"method":"event.window_removed","params":{{"id":{}}}}}"#, id),
                                ipc_bridge::CompositorEvent::FocusChanged { id } =>
                                    format!(r#"{{"method":"event.window_focused","params":{{"id":{}}}}}"#,
                                        id.map(|i| i.to_string()).unwrap_or("null".into())),
                                ipc_bridge::CompositorEvent::WindowMinimized { id, minimized } =>
                                    format!(r#"{{"method":"event.window_minimized","params":{{"id":{},"minimized":{}}}}}"#, id, minimized),
                                ipc_bridge::CompositorEvent::WindowTitleChanged { id, title } =>
                                    format!(r#"{{"method":"event.window_title","params":{{"id":{},"title":{}}}}}"#,
                                        id, serde_json::to_string(title).unwrap_or_default()),
                                _ => continue,
                            };
                            let mut msg = method;
                            msg.push('\n');
                            stream.write_all(msg.as_bytes()).await.ok();
                        }
                    }
                    tokio::time::sleep(tokio::time::Duration::from_millis(16)).await;
                }
            });
        }
    }

    info!("CM Compositor ready on {}", socket_name);

    // Main event loop — ~60fps
    loop {
        event_loop
            .dispatch(
                Some(std::time::Duration::from_millis(16)),
                &mut state,
            )
            .map_err(|e| anyhow::anyhow!("Dispatch: {}", e))?;

        state.refresh_space();

        if state.should_exit {
            info!("CM Compositor exiting");
            break;
        }
    }

    Ok(())
}
