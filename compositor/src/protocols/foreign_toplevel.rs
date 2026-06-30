use smithay::desktop::Window;
use smithay::reexports::wayland_server::{
    Client, DataInit, Dispatch, DisplayHandle, GlobalDispatch, New, Resource,
};
use std::sync::{Arc, Mutex};
use tracing::{debug, info};

use wayland_protocols_wlr::foreign_toplevel::v1::server::{
    zwlr_foreign_toplevel_handle_v1::{self, ZwlrForeignToplevelHandleV1, State as ToplevelState},
    zwlr_foreign_toplevel_manager_v1::{self, ZwlrForeignToplevelManagerV1},
};

use crate::state::CmState;

pub struct ForeignToplevelManagerState {
    pub handles: Vec<ZwlrForeignToplevelHandleV1>,
}

impl ForeignToplevelManagerState {
    pub fn new(display: &DisplayHandle) -> Self {
        display.create_global::<CmState, ZwlrForeignToplevelManagerV1, _>(3, ());
        Self { handles: Vec::new() }
    }

    /// Notify all managers of a new window
    pub fn window_created(&mut self, title: &str, app_id: &str) {
        for handle in &self.handles {
            handle.title(title.to_string());
            handle.app_id(app_id.to_string());
            handle.state(vec![]);
            handle.done();
        }
        info!("ForeignToplevel: window created '{}'", title);
    }

    /// Notify all managers of window removal
    pub fn window_closed(&mut self, handle: &ZwlrForeignToplevelHandleV1) {
        handle.closed();
        self.handles.retain(|h| h != handle);
    }

    /// Update window title
    pub fn window_title_changed(&mut self, handle: &ZwlrForeignToplevelHandleV1, title: &str) {
        handle.title(title.to_string());
        handle.done();
    }

    /// Update window state (focused, maximized, minimized)
    pub fn window_state_changed(
        &mut self,
        handle: &ZwlrForeignToplevelHandleV1,
        focused: bool,
        maximized: bool,
        minimized: bool,
    ) {
        let mut states = Vec::new();
        if maximized { states.push(ToplevelState::Maximized as u32); }
        if minimized { states.push(ToplevelState::Minimized as u32); }
        if focused   { states.push(ToplevelState::Activated as u32); }
        handle.state(states.into_iter().flat_map(|s| s.to_ne_bytes()).collect());
        handle.done();
    }
}

impl GlobalDispatch<ZwlrForeignToplevelManagerV1, ()> for CmState {
    fn bind(
        _state: &mut CmState,
        _handle: &DisplayHandle,
        _client: &Client,
        resource: New<ZwlrForeignToplevelManagerV1>,
        _global_data: &(),
        data_init: &mut DataInit<'_, CmState>,
    ) {
        data_init.init(resource, ());
        info!("ForeignToplevel: manager bound");
    }
}

impl Dispatch<ZwlrForeignToplevelManagerV1, ()> for CmState {
    fn request(
        _state: &mut CmState,
        _client: &Client,
        _manager: &ZwlrForeignToplevelManagerV1,
        request: zwlr_foreign_toplevel_manager_v1::Request,
        _data: &(),
        _display: &DisplayHandle,
        _data_init: &mut DataInit<'_, CmState>,
    ) {
        match request {
            zwlr_foreign_toplevel_manager_v1::Request::Stop => {
                debug!("ForeignToplevel: manager stop");
            }
            _ => {}
        }
    }
}

impl Dispatch<ZwlrForeignToplevelHandleV1, ()> for CmState {
    fn request(
        state: &mut CmState,
        _client: &Client,
        handle: &ZwlrForeignToplevelHandleV1,
        request: zwlr_foreign_toplevel_handle_v1::Request,
        _data: &(),
        _display: &DisplayHandle,
        _data_init: &mut DataInit<'_, CmState>,
    ) {
        match request {
            zwlr_foreign_toplevel_handle_v1::Request::Activate { seat: _ } => {
                // Find matching window and focus it
                debug!("ForeignToplevel: activate request");
            }
            zwlr_foreign_toplevel_handle_v1::Request::Close => {
                // Close the window
                debug!("ForeignToplevel: close request");
            }
            zwlr_foreign_toplevel_handle_v1::Request::SetMaximized => {
                debug!("ForeignToplevel: maximize");
            }
            zwlr_foreign_toplevel_handle_v1::Request::UnsetMaximized => {
                debug!("ForeignToplevel: unmaximize");
            }
            zwlr_foreign_toplevel_handle_v1::Request::SetMinimized => {
                debug!("ForeignToplevel: minimize");
            }
            zwlr_foreign_toplevel_handle_v1::Request::UnsetMinimized => {
                debug!("ForeignToplevel: unminimize");
            }
            zwlr_foreign_toplevel_handle_v1::Request::Destroy => {}
            _ => {}
        }
    }
}
