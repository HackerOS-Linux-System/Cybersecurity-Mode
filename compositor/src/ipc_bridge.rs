use serde::{Deserialize, Serialize};

/// Events emitted by compositor, consumed by CM shell
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum CompositorEvent {
    WindowAdded       { id: u64, title: String, app_id: String },
    WindowRemoved     { id: u64 },
    WindowTitleChanged{ id: u64, title: String },
    WindowMinimized   { id: u64, minimized: bool },
    FocusChanged      { id: Option<u64> },
    WorkspaceSwitched { workspace: usize },
    OutputHotplugged  { name: String, width: i32, height: i32, refresh: i32, connected: bool },
}

/// Commands from CM shell to compositor
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum CompositorCommand {
    RaiseWindow   { id: u64 },
    MinimizeWindow{ id: u64 },
    CloseWindow   { id: u64 },
    SwitchWorkspace{ workspace: usize },
    MoveToWorkspace{ id: u64, workspace: usize },
    SetWallpaper  { path: String },
    Lock,
    Screenshot    { path: String },
}
