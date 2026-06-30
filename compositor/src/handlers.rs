use smithay::{
    delegate_compositor, delegate_data_device, delegate_fractional_scale,
    delegate_layer_shell, delegate_output, delegate_primary_selection,
    delegate_seat, delegate_shm, delegate_viewporter,
    delegate_xdg_shell, delegate_xdg_output,
    desktop::{PopupKind, Space, Window},
    input::{Seat, SeatHandler, SeatState},
    reexports::wayland_server::{
        protocol::{wl_output::WlOutput, wl_seat::WlSeat, wl_surface::WlSurface},
        Resource,
    },
    utils::{Serial, SERIAL_COUNTER},
    wayland::{
        buffer::BufferHandler,
        compositor::{CompositorClientState, CompositorHandler, CompositorState},
        fractional_scale::{FractionalScaleHandler, FractionalScaleManagerState},
        output::OutputHandler,
        selection::{
            data_device::{
                ClientDndGrabHandler, DataDeviceHandler, DataDeviceState,
                ServerDndGrabHandler,
            },
            primary_selection::{PrimarySelectionHandler, PrimarySelectionState},
            SelectionHandler,
        },
        shell::{
            wlr_layer::{Layer, WlrLayerShellHandler, WlrLayerShellState, LayerSurface as WlrLayerSurface},
            xdg::{
                PopupSurface, PositionerState, ToplevelSurface,
                XdgShellHandler, XdgShellState, XdgToplevelSurfaceData,
            },
        },
        shm::{ShmHandler, ShmState},
        viewporter::ViewporterHandler,
    },
};
use tracing::{debug, info};

use crate::state::{CmState, ClientState};

// ── Compositor ────────────────────────────────────────────────────────────

impl CompositorHandler for CmState {
    fn compositor_state(&mut self) -> &mut CompositorState {
        &mut self.compositor_state
    }
    fn client_compositor_state<'a>(
        &self, client: &'a smithay::reexports::wayland_server::Client,
    ) -> &'a CompositorClientState {
        &client.get_data::<ClientState>().unwrap().compositor_client_state
    }
    fn commit(&mut self, surface: &WlSurface) {
        if let Some(output) = self.space.outputs().next().cloned() {
            smithay::desktop::utils::send_frames_surface_tree(
                surface, &output, self.clock.now(),
                None, |_, _| Some(Default::default()),
            );
        }
    }
}

delegate_compositor!(CmState);

// ── XDG Shell ─────────────────────────────────────────────────────────────

impl XdgShellHandler for CmState {
    fn xdg_shell_state(&mut self) -> &mut XdgShellState {
        &mut self.xdg_shell_state
    }

    fn new_toplevel(&mut self, surface: ToplevelSurface) {
        let window = Window::new_wayland_window(surface);
        let title  = window.title().unwrap_or_default();
        let app_id = window.app_id().unwrap_or_default();

        // Place in usable area (excluding taskbar)
        let count = self.space.elements().count();
        let tb_h  = self.config.taskbar_height as i32;
        let x = 20 + (count as i32 * 24).min(self.output_size.w / 2);
        let y = 20 + (count as i32 * 24).min((self.output_size.h - tb_h) / 2);

        self.space.map_element(window.clone(), (x, y), true);
        self.foreign_toplevel.window_created(&title, &app_id);
        info!("New toplevel: '{}' ({})", title, app_id);

        // Register in window map and notify shell
        let id = self.next_window_id();
        self.register_window(id, &title, &app_id);
        self.notify_ipc_window_added(id, &title, &app_id);
        self.notify_ipc_focus(Some(id));
    }

    fn new_popup(&mut self, surface: PopupSurface, _positioner: PositionerState) {
        self.popup_manager.track_popup(PopupKind::Xdg(surface)).ok();
    }

    fn toplevel_destroyed(&mut self, surface: ToplevelSurface) {
        let windows: Vec<_> = self.space.elements().cloned().collect();
        for w in windows {
            if w.wl_surface().map(|s| s == *surface.wl_surface()).unwrap_or(false) {
                let id = self.window_id_for(&w);
                self.space.unmap_elem(&w);
                if let Some(id) = id {
                    self.unregister_window(id);
                    self.notify_ipc_window_removed(id);
                }
                break;
            }
        }
    }

    fn grab(&mut self, _surface: PopupSurface, _seat: WlSeat, _serial: Serial) {}

    fn reposition_request(
        &mut self, _surface: PopupSurface,
        _positioner: PositionerState, _token: u32,
    ) {}

    fn move_request(&mut self, surface: ToplevelSurface, _seat: WlSeat, _serial: Serial) {
        // Interactive move — track pointer and update window position
        let window = self.space.elements()
            .find(|w| w.wl_surface().map(|s| s == *surface.wl_surface()).unwrap_or(false))
            .cloned();
        if let Some(w) = window {
            let loc = self.input.pointer_location;
            self.space.map_element(w, (loc.x as i32, loc.y as i32), true);
        }
    }

    fn resize_request(
        &mut self, _surface: ToplevelSurface, _seat: WlSeat,
        _serial: Serial, _edges: smithay::wayland::shell::xdg::ResizeEdge,
    ) {}

    fn maximize_request(&mut self, surface: ToplevelSurface) {
        let output = self.space.outputs().next().cloned();
        if let Some(output) = output {
            let zone = crate::protocols::layer_shell::compute_usable_area(&output);
            surface.with_pending_state(|s| {
                s.size = Some(zone.size);
                s.states.set(smithay::reexports::wayland_protocols::xdg::shell::server::xdg_toplevel::State::Maximized);
            });
            surface.send_configure();
            // Move to usable area top-left
            let window = self.space.elements()
                .find(|w| w.wl_surface().map(|s| s == *surface.wl_surface()).unwrap_or(false))
                .cloned();
            if let Some(w) = window {
                self.space.map_element(w, zone.loc, false);
            }
        }
    }

    fn unmaximize_request(&mut self, surface: ToplevelSurface) {
        surface.with_pending_state(|s| {
            s.size = None;
            s.states.unset(smithay::reexports::wayland_protocols::xdg::shell::server::xdg_toplevel::State::Maximized);
        });
        surface.send_configure();
    }

    fn fullscreen_request(
        &mut self, surface: ToplevelSurface,
        _output: Option<WlOutput>,
    ) {
        if let Some(output) = self.space.outputs().next() {
            let size = output.current_mode().map(|m| m.size).unwrap_or((1920, 1080).into());
            surface.with_pending_state(|s| {
                s.size = Some(size.to_logical(1));
                s.states.set(smithay::reexports::wayland_protocols::xdg::shell::server::xdg_toplevel::State::Fullscreen);
            });
            surface.send_configure();
        }
    }

    fn unfullscreen_request(&mut self, surface: ToplevelSurface) {
        surface.with_pending_state(|s| {
            s.size = None;
            s.states.unset(smithay::reexports::wayland_protocols::xdg::shell::server::xdg_toplevel::State::Fullscreen);
        });
        surface.send_configure();
    }
}

delegate_xdg_shell!(CmState);

// ── Layer Shell ───────────────────────────────────────────────────────────

impl WlrLayerShellHandler for CmState {
    fn shell_state(&mut self) -> &mut WlrLayerShellState {
        &mut self.layer_shell_state
    }
    fn new_layer_surface(
        &mut self, surface: WlrLayerSurface,
        output: Option<WlOutput>, _layer: Layer, namespace: String,
    ) {
        let out = self.space.outputs().next().cloned();
        if let Some(out) = out {
            use smithay::desktop::LayerSurface;
            smithay::desktop::layer_map_for_output(&out)
                .map_layer(&LayerSurface::new(surface, namespace)).ok();
            info!("Layer surface mapped");
        }
    }
    fn layer_destroyed(&mut self, surface: WlrLayerSurface) {
        use smithay::desktop::LayerSurface;
        let ls = LayerSurface::new(surface, String::new());
        for out in self.space.outputs().cloned().collect::<Vec<_>>() {
            smithay::desktop::layer_map_for_output(&out).unmap_layer(&ls);
        }
    }
}

delegate_layer_shell!(CmState);

// ── SHM ──────────────────────────────────────────────────────────────────

impl ShmHandler for CmState {
    fn shm_state(&self) -> &ShmState { &self.shm_state }
}

impl BufferHandler for CmState {
    fn buffer_destroyed(
        &mut self,
        _buf: &smithay::reexports::wayland_server::protocol::wl_buffer::WlBuffer,
    ) {}
}

delegate_shm!(CmState);

// ── Seat ──────────────────────────────────────────────────────────────────

impl SeatHandler for CmState {
    type KeyboardFocus = Window;
    type PointerFocus  = Window;
    type TouchFocus    = Window;

    fn seat_state(&mut self) -> &mut SeatState<Self> { &mut self.seat_state }

    fn cursor_image(
        &mut self, _seat: &Seat<Self>,
        image: smithay::input::pointer::CursorImageStatus,
    ) {
        self.cursor_status = image;
    }

    fn focus_changed(&mut self, _seat: &Seat<Self>, focused: Option<&Window>) {
        // Notify foreign toplevel about focus change
        if let Some(w) = focused {
            let _title  = w.title().unwrap_or_default();
            let _app_id = w.app_id().unwrap_or_default();
        }
    }
}

delegate_seat!(CmState);

// ── Output ────────────────────────────────────────────────────────────────

impl OutputHandler for CmState {}
delegate_output!(CmState);
delegate_xdg_output!(CmState);

// ── Viewporter ────────────────────────────────────────────────────────────

impl ViewporterHandler for CmState {
    fn viewporter_state(&self) -> &smithay::wayland::viewporter::ViewporterState {
        &self.viewporter_state
    }
}
delegate_viewporter!(CmState);

// ── Fractional Scale ──────────────────────────────────────────────────────

impl FractionalScaleHandler for CmState {
    fn new_fractional_scale(
        &mut self,
        surface: WlSurface,
    ) {
        use smithay::wayland::fractional_scale::with_fractional_scale;
        with_fractional_scale(
            surface.data_map(),
            |fractional_scale| {
                fractional_scale.set_preferred_scale(
                    self.output_manager
                        .outputs()
                        .next()
                        .map(|o| o.current_scale().fractional_scale())
                        .unwrap_or(1.0),
                );
            },
        );
    }
}
delegate_fractional_scale!(CmState);

// ── Data Device ───────────────────────────────────────────────────────────

impl SelectionHandler for CmState {
    type SelectionUserData = ();
}

impl DataDeviceHandler for CmState {
    fn data_device_state(&self) -> &DataDeviceState { &self.data_device_state }
}

impl ClientDndGrabHandler for CmState {}
impl ServerDndGrabHandler for CmState {}
delegate_data_device!(CmState);

// ── Primary Selection ─────────────────────────────────────────────────────

impl PrimarySelectionHandler for CmState {
    fn primary_selection_state(&self) -> &PrimarySelectionState {
        &self.primary_selection_state
    }
}
delegate_primary_selection!(CmState);
