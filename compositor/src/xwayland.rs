use anyhow::Result;
use smithay::{
    desktop::Window,
    utils::{Logical, Point, Rectangle},
    xwayland::{
        xwm::{Reorder, ResizeEdge as X11ResizeEdge, WmWindowProperty, X11Wm, XwmHandler, XwmId},
        X11Surface, XWayland, XWaylandClientData, XWaylandEvent,
    },
};
use tracing::{debug, info, warn};
use crate::state::CmState;

pub fn init(state: &mut CmState) -> Result<()> {
    let (xwayland, source) = XWayland::new(&state.display_handle)
        .map_err(|e| anyhow::anyhow!("XWayland: {}", e))?;

    state.loop_handle
        .insert_source(source, move |event, _, state| {
            handle_xwayland_event(state, event);
        })
        .map_err(|e| anyhow::anyhow!("XWayland source: {}", e))?;

    state.xwayland = Some(xwayland);
    info!("XWayland initialized — waiting for ready event");
    Ok(())
}

fn handle_xwayland_event(state: &mut CmState, event: XWaylandEvent) {
    match event {
        XWaylandEvent::Ready { connection, client, client_fd: _, display } => {
            info!("XWayland ready on DISPLAY=:{}", display);
            std::env::set_var("DISPLAY", format!(":{}", display));

            match X11Wm::start_wm(state.loop_handle.clone(), connection, client) {
                Ok(wm) => {
                    info!("X11 WM started (DISPLAY=:{})", display);
                    state.x11_wm = Some(wm);
                }
                Err(e) => warn!("X11 WM start failed: {}", e),
            }
        }
        XWaylandEvent::Exited => {
            warn!("XWayland exited");
            state.xwayland = None;
            state.x11_wm   = None;
        }
    }
}

// ── XwmHandler — called by smithay for all X11 window events ─────────────

impl XwmHandler for CmState {
    fn xwm_state(&mut self, _xwm: XwmId) -> &mut X11Wm {
        self.x11_wm.as_mut().expect("X11Wm not initialized")
    }

    fn new_window(&mut self, _xwm: XwmId, window: X11Surface) {
        debug!("X11 new window: {:?} class={:?}", window.title(), window.class());
    }

    fn new_override_redirect_window(&mut self, _xwm: XwmId, window: X11Surface) {
        // Menus, tooltips, popups — map immediately without WM intervention
        debug!("X11 override-redirect: {:?}", window.title());
        window.set_mapped(true).ok();
        let geo = window.geometry();
        self.space.map_element(
            Window::new_x11_window(window),
            (geo.loc.x, geo.loc.y),
            false,
        );
    }

    fn map_window_request(&mut self, _xwm: XwmId, window: X11Surface) {
        let title  = window.title().unwrap_or_default();
        let class  = window.class().unwrap_or_default();
        info!("X11 map window: '{}' class='{}'", title, class);

        // Compute placement in usable area
        let count = self.space.elements().count();
        let loc = if let Some(output) = self.space.outputs().next() {
            let zone = crate::protocols::layer_shell::compute_usable_area(output);
            Point::from((
                zone.loc.x + (count as i32 * 22).min(zone.size.w / 3),
                zone.loc.y + (count as i32 * 22).min(zone.size.h / 3),
            ))
        } else {
            Point::from((20 + count as i32 * 22, 20 + count as i32 * 22))
        };

        // Try to set initial geometry from hints
        let mut geo = window.geometry();
        if geo.size.w < 100 { geo.size.w = 900; }
        if geo.size.h < 100 { geo.size.h = 600; }
        geo.loc = loc.into();
        window.configure(geo).ok();
        window.set_mapped(true).ok();

        let win = Window::new_x11_window(window);
        self.space.map_element(win.clone(), loc, true);

        // Notify taskbar via IPC
        let title2  = win.title().unwrap_or_default();
        let app_id2 = win.app_id().unwrap_or_default();
        self.foreign_toplevel.window_created(&title2, &app_id2);

        // IPC: push window to taskbar
        let id = self.next_window_id();
        self.notify_ipc_window_added(id, &title2, &app_id2);
    }

    fn map_window_notify(&mut self, _xwm: XwmId, window: X11Surface) {
        debug!("X11 mapped: {:?}", window.title());
    }

    fn unmapped_window(&mut self, _xwm: XwmId, window: X11Surface) {
        let title = window.title().unwrap_or_default();
        debug!("X11 unmapped: '{}'", title);
        let windows: Vec<_> = self.space.elements().cloned().collect();
        for w in windows {
            if w.wl_surface().as_ref() == window.wl_surface().ok().as_ref() {
                let id = self.window_id_for(&w);
                self.space.unmap_elem(&w);
                if let Some(id) = id { self.notify_ipc_window_removed(id); }
                break;
            }
        }
    }

    fn destroyed_window(&mut self, _xwm: XwmId, window: X11Surface) {
        debug!("X11 destroyed: {:?}", window.title());
    }

    fn configure_request(
        &mut self, _xwm: XwmId,
        window: X11Surface,
        x: Option<i32>, y: Option<i32>,
        w: Option<u32>, h: Option<u32>,
        _reorder: Option<Reorder>,
    ) {
        let mut geo = window.geometry();
        if let Some(x) = x { geo.loc.x = x; }
        if let Some(y) = y { geo.loc.y = y; }
        if let Some(w) = w { geo.size.w = w as i32; }
        if let Some(h) = h { geo.size.h = h as i32; }
        window.configure(geo).ok();
    }

    fn configure_notify(
        &mut self, _xwm: XwmId,
        window: X11Surface,
        geometry: Rectangle<i32, Logical>,
        _above: Option<u32>,
    ) {
        let windows: Vec<_> = self.space.elements().cloned().collect();
        for w in windows {
            if w.wl_surface().as_ref() == window.wl_surface().ok().as_ref() {
                self.space.map_element(w, geometry.loc, false);
                break;
            }
        }
    }

    fn property_notify(
        &mut self, _xwm: XwmId,
        window: X11Surface,
        property: WmWindowProperty,
    ) {
        // Update title in taskbar when _NET_WM_NAME changes
        if let WmWindowProperty::Title = property {
            let new_title = window.title().unwrap_or_default();
            debug!("X11 title changed: '{}'", new_title);
            let windows: Vec<_> = self.space.elements().cloned().collect();
            for w in &windows {
                if w.wl_surface().as_ref() == window.wl_surface().ok().as_ref() {
                    let id = self.window_id_for(w);
                    if let Some(id) = id {
                        self.notify_ipc_window_updated(id, &new_title);
                    }
                    break;
                }
            }
        }
    }

    fn resize_request(
        &mut self, _xwm: XwmId,
        window: X11Surface, _button: u32, _resize_edge: X11ResizeEdge,
    ) {
        // Interactive resize — track pointer delta
        let ptr_loc = self.input.pointer_location;
        let geo = window.geometry();
        // Simple: just allow the configure_request to handle it
        let _ = (ptr_loc, geo);
    }

    fn move_request(&mut self, _xwm: XwmId, window: X11Surface, _button: u32) {
        let ptr_loc = self.input.pointer_location;
        let windows: Vec<_> = self.space.elements().cloned().collect();
        for w in windows {
            if w.wl_surface().as_ref() == window.wl_surface().ok().as_ref() {
                self.space.map_element(w, (ptr_loc.x as i32, ptr_loc.y as i32), true);
                break;
            }
        }
    }

    fn fullscreen_request(&mut self, _xwm: XwmId, window: X11Surface) {
        let (sw, sh) = (self.output_size.w, self.output_size.h);
        window.set_fullscreen(true).ok();
        window.configure(Rectangle::from_loc_and_size((0,0),(sw,sh))).ok();
    }
    fn unfullscreen_request(&mut self, _xwm: XwmId, window: X11Surface) {
        window.set_fullscreen(false).ok();
    }
    fn maximize_request(&mut self, _xwm: XwmId, window: X11Surface) {
        if let Some(output) = self.space.outputs().next() {
            let zone = crate::protocols::layer_shell::compute_usable_area(output);
            window.set_maximized(true).ok();
            window.configure(zone).ok();
        }
    }
    fn unmaximize_request(&mut self, _xwm: XwmId, window: X11Surface) {
        window.set_maximized(false).ok();
    }
    fn minimize_request(&mut self, _xwm: XwmId, window: X11Surface) {
        window.set_minimized(true).ok();
        let windows: Vec<_> = self.space.elements().cloned().collect();
        for w in windows {
            if w.wl_surface().as_ref() == window.wl_surface().ok().as_ref() {
                let id = self.window_id_for(&w);
                self.space.unmap_elem(&w);
                if let Some(id) = id {
                    self.notify_ipc_window_minimized(id, true);
                }
                break;
            }
        }
    }
    fn unminimize_request(&mut self, _xwm: XwmId, window: X11Surface) {
        window.set_minimized(false).ok();
    }
}
