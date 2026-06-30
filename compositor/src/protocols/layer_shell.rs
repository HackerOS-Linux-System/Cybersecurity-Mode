use smithay::{
    delegate_layer_shell,
    desktop::{LayerSurface, LayerMap, PopupManager, Space, Window},
    output::Output,
    reexports::wayland_server::protocol::wl_output::WlOutput,
    utils::{Logical, Physical, Point, Rectangle, Size},
    wayland::shell::wlr_layer::{
        Layer, LayerSurface as WlrLayerSurface, LayerSurfaceData,
        WlrLayerShellHandler, WlrLayerShellState,
    },
};
use tracing::{debug, info};

use crate::state::CmState;

impl WlrLayerShellHandler for CmState {
    fn shell_state(&mut self) -> &mut WlrLayerShellState {
        &mut self.layer_shell_state
    }

    fn new_layer_surface(
        &mut self,
        surface: WlrLayerSurface,
        output: Option<WlOutput>,
        layer: Layer,
        namespace: String,
    ) {
        let output = self.space.outputs().next().cloned();

        if let Some(output) = output {
            smithay::desktop::layer_map_for_output(&output)
                .map_layer(&LayerSurface::new(surface, namespace)).ok();
            info!("New layer surface — layer: {:?}", layer);
        }
    }

    fn layer_destroyed(&mut self, surface: WlrLayerSurface) {
        let layer_surf = LayerSurface::new(surface, String::new());
        for output in self.space.outputs().cloned().collect::<Vec<_>>() {
            let layer_map = smithay::desktop::layer_map_for_output(&output);
            layer_map.unmap_layer(&layer_surf);
        }
    }
}

delegate_layer_shell!(CmState);

/// Compute usable area excluding anchored layer surfaces (taskbar)
pub fn compute_usable_area(output: &Output) -> Rectangle<i32, Logical> {
    let output_size = output
        .current_mode()
        .map(|m| m.size.to_logical(output.current_scale().integer_scale()))
        .unwrap_or_else(|| (1920, 1080).into());

    let layer_map = smithay::desktop::layer_map_for_output(output);
    let zone = layer_map.non_exclusive_zone();

    Rectangle::from_loc_and_size(
        (zone.left, zone.top),
        (output_size.w - zone.left - zone.right,
         output_size.h - zone.top - zone.bottom),
    )
}
