use smithay::{
    desktop::{PopupManager, Space, Window, LayerSurface},
    input::{Seat, SeatState, pointer::CursorImageStatus},
    reexports::{
        calloop::{EventLoop, LoopHandle, LoopSignal},
        wayland_server::{
            backend::{ClientData, ClientId, DisconnectReason},
            Display, DisplayHandle,
            protocol::wl_surface::WlSurface,
        },
    },
    utils::{Clock, Logical, Monotonic, Rectangle, Size},
    wayland::{
        compositor::CompositorState,
        output::OutputManagerState,
        shell::xdg::{XdgShellState, PopupSurface, ToplevelSurface},
        shell::wlr_layer::WlrLayerShellState,
        shm::ShmState,
        socket::ListeningSocketSource,
        selection::data_device::DataDeviceState,
        selection::primary_selection::PrimarySelectionState,
        viewporter::ViewporterState,
        fractional_scale::FractionalScaleManagerState,
    },
    xwayland::xwm::X11Wm,
};
use std::sync::Arc;
use anyhow::Result;
use tracing::info;

use crate::input::InputState;
use crate::protocols::{
    foreign_toplevel::ForeignToplevelManagerState,
    screencopy::ScreencopyManagerState,
};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CompositorMode { Environment, Mode }

pub struct CmConfig {
    pub enable_xwayland:      bool,
    pub wallpaper:            String,
    pub taskbar_height:       u32,
    pub animation_duration_ms: u32,
    pub enable_blur:          bool,
    pub mode:                 CompositorMode,
    pub workspace_count:      usize,
}

impl Default for CmConfig {
    fn default() -> Self {
        Self {
            enable_xwayland:      true,
            wallpaper:            "/usr/share/wallpapers/HackerOS-Wallpapers/Wallpaper23.png".into(),
            taskbar_height:       40,
            animation_duration_ms: 200,
            enable_blur:          true,
            mode:                 CompositorMode::Environment,
            workspace_count:      4,
        }
    }
}

/// Per-window metadata tracked by compositor
#[derive(Debug, Clone)]
pub struct WindowMeta {
    pub id:        u64,
    pub title:     String,
    pub app_id:    String,
    pub workspace: usize,
    pub minimized: bool,
}

pub struct CmState {
    // Smithay core
    pub display_handle: DisplayHandle,
    pub loop_handle:    LoopHandle<'static, CmState>,
    pub loop_signal:    LoopSignal,
    pub clock:          Clock<Monotonic>,

    // Wayland protocols
    pub compositor_state:       CompositorState,
    pub xdg_shell_state:        XdgShellState,
    pub layer_shell_state:      WlrLayerShellState,
    pub shm_state:              ShmState,
    pub output_manager:         OutputManagerState,
    pub seat_state:             SeatState<CmState>,
    pub data_device_state:      DataDeviceState,
    pub primary_selection_state: PrimarySelectionState,
    pub popup_manager:          PopupManager,
    pub viewporter_state:       ViewporterState,
    pub fractional_scale_state: FractionalScaleManagerState,

    // Extra protocols
    pub foreign_toplevel: ForeignToplevelManagerState,
    pub screencopy:       ScreencopyManagerState,

    // Desktop
    pub space: Space<Window>,
    pub seat:  Seat<CmState>,

    // Input
    pub input: InputState,

    // XWayland
    pub xwayland: Option<smithay::xwayland::XWayland>,
    pub x11_wm:   Option<X11Wm>,

    // CM state
    pub config:           CmConfig,
    pub should_exit:      bool,
    pub cursor_status:    CursorImageStatus,
    pub output_size:      Size<i32, Logical>,
    pub active_workspace: usize,

    // Window tracking: id -> meta
    pub window_meta:      std::collections::HashMap<u64, WindowMeta>,
    pub next_win_id:      u64,

    // Workspace window tracking
    pub workspace_windows: Vec<Vec<u64>>,

    // IPC channel to notify CM shell about window changes
    pub ipc_tx: Option<tokio::sync::mpsc::UnboundedSender<crate::ipc_bridge::CompositorEvent>>,
}

impl CmState {
    pub fn new(
        event_loop: &mut EventLoop<'static, CmState>,
        display:    &mut Display<CmState>,
        mode:       CompositorMode,
        socket_name: String,
    ) -> Result<Self> {
        let display_handle  = display.handle();
        let loop_handle     = event_loop.handle();
        let loop_signal     = event_loop.get_signal();
        let clock           = Clock::new();

        let compositor_state        = CompositorState::new::<CmState>(&display_handle);
        let xdg_shell_state         = XdgShellState::new::<CmState>(&display_handle);
        let layer_shell_state       = WlrLayerShellState::new::<CmState>(&display_handle);
        let shm_state               = ShmState::new::<CmState>(&display_handle, vec![]);
        let output_manager          = OutputManagerState::new_with_xdg_output::<CmState>(&display_handle);
        let mut seat_state          = SeatState::new();
        let data_device_state       = DataDeviceState::new::<CmState>(&display_handle);
        let primary_selection_state = PrimarySelectionState::new::<CmState>(&display_handle);
        let popup_manager           = PopupManager::default();
        let viewporter_state        = ViewporterState::new::<CmState>(&display_handle);
        let fractional_scale_state  = FractionalScaleManagerState::new::<CmState>(&display_handle);
        let foreign_toplevel        = ForeignToplevelManagerState::new(&display_handle);
        let screencopy              = ScreencopyManagerState::new(&display_handle);

        let seat = seat_state.new_wl_seat(&display_handle, "seat-0");

        let source = ListeningSocketSource::with_name(socket_name.clone())
            .map_err(|e| anyhow::anyhow!("Socket: {}", e))?;
        loop_handle.insert_source(source, |client_stream, _, state| {
            if let Err(e) = state.display_handle.insert_client(
                client_stream, Arc::new(ClientState::default()),
            ) { tracing::error!("Client insert failed: {}", e); }
        }).map_err(|e| anyhow::anyhow!("Socket source: {}", e))?;

        info!("Wayland socket: {}", socket_name);

        let config          = CmConfig { mode, ..Default::default() };
        let workspace_count = config.workspace_count;

        Ok(Self {
            display_handle, loop_handle, loop_signal, clock,
            compositor_state, xdg_shell_state, layer_shell_state,
            shm_state, output_manager, seat_state, data_device_state,
            primary_selection_state, popup_manager, viewporter_state,
            fractional_scale_state, foreign_toplevel, screencopy,
            space: Space::default(),
            seat,
            input: InputState::default(),
            xwayland: None,
            x11_wm: None,
            config,
            should_exit: false,
            cursor_status: CursorImageStatus::default(),
            output_size: (1920, 1080).into(),
            active_workspace: 0,
            window_meta: std::collections::HashMap::new(),
            next_win_id: 1,
            workspace_windows: vec![Vec::new(); workspace_count],
            ipc_tx: None,
        })
    }

    pub fn exit(&mut self) {
        self.should_exit = true;
        self.loop_signal.stop();
    }

    // ── Window ID tracking ─────────────────────────────────────────────────

    pub fn next_window_id(&mut self) -> u64 {
        let id = self.next_win_id;
        self.next_win_id += 1;
        id
    }

    pub fn window_id_for(&self, window: &Window) -> Option<u64> {
        // Find by surface reference via meta title match — simplified
        let title  = window.title().unwrap_or_default();
        let app_id = window.app_id().unwrap_or_default();
        self.window_meta.values()
            .find(|m| m.title == title && m.app_id == app_id)
            .map(|m| m.id)
    }

    pub fn register_window(&mut self, id: u64, title: &str, app_id: &str) {
        self.window_meta.insert(id, WindowMeta {
            id, title: title.into(), app_id: app_id.into(),
            workspace: self.active_workspace, minimized: false,
        });
        if let Some(ws) = self.workspace_windows.get_mut(self.active_workspace) {
            ws.push(id);
        }
    }

    pub fn unregister_window(&mut self, id: u64) {
        self.window_meta.remove(&id);
        for ws in self.workspace_windows.iter_mut() {
            ws.retain(|&wid| wid != id);
        }
    }

    // ── IPC notifications to CM shell ──────────────────────────────────────

    pub fn notify_ipc_window_added(&self, id: u64, title: &str, app_id: &str) {
        if let Some(tx) = &self.ipc_tx {
            tx.send(crate::ipc_bridge::CompositorEvent::WindowAdded {
                id, title: title.into(), app_id: app_id.into(),
            }).ok();
        }
    }

    pub fn notify_ipc_window_removed(&self, id: u64) {
        if let Some(tx) = &self.ipc_tx {
            tx.send(crate::ipc_bridge::CompositorEvent::WindowRemoved { id }).ok();
        }
    }

    pub fn notify_ipc_window_updated(&self, id: u64, title: &str) {
        if let Some(tx) = &self.ipc_tx {
            tx.send(crate::ipc_bridge::CompositorEvent::WindowTitleChanged {
                id, title: title.into(),
            }).ok();
        }
    }

    pub fn notify_ipc_window_minimized(&self, id: u64, minimized: bool) {
        if let Some(tx) = &self.ipc_tx {
            tx.send(crate::ipc_bridge::CompositorEvent::WindowMinimized { id, minimized }).ok();
        }
    }

    pub fn notify_ipc_focus(&self, id: Option<u64>) {
        if let Some(tx) = &self.ipc_tx {
            tx.send(crate::ipc_bridge::CompositorEvent::FocusChanged { id }).ok();
        }
    }

    pub fn notify_ipc_workspace(&self, workspace: usize) {
        if let Some(tx) = &self.ipc_tx {
            tx.send(crate::ipc_bridge::CompositorEvent::WorkspaceSwitched { workspace }).ok();
        }
    }
}

// ── Client data ────────────────────────────────────────────────────────────

#[derive(Default)]
pub struct ClientState {
    pub compositor_client_state: smithay::wayland::compositor::CompositorClientState,
}

impl ClientData for ClientState {
    fn initialized(&self, _client_id: ClientId) {}
    fn disconnected(&self, _client_id: ClientId, _reason: DisconnectReason) {}
}
