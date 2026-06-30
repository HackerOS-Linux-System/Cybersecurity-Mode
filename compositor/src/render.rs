use smithay::{
    backend::{
        renderer::{
            element::{
                surface::WaylandSurfaceRenderElement,
                utils::draw_render_elements,
            },
            gles::GlesRenderer,
            Renderer,
        },
        winit::WinitGraphicsBackend,
    },
    desktop::{Space, Window},
    output::Output,
    utils::{Physical, Rectangle, Scale, Transform, Point},
};
use tracing::debug;
use crate::state::CmState;

type CmRenderElement = WaylandSurfaceRenderElement<GlesRenderer>;

/// Render one frame via winit backend (smithay 0.7)
pub fn render_frame(state: &mut CmState, backend: &mut WinitGraphicsBackend<GlesRenderer>) {
    let output = match state.space.outputs().next() {
        Some(o) => o.clone(),
        None => return,
    };

    let output_size = output.current_mode()
        .map(|m| m.size)
        .unwrap_or_else(|| (1920, 1080).into());
    let scale = Scale::from(output.current_scale().fractional_scale());

    let bg: smithay::backend::renderer::Color32F = match state.config.mode {
        crate::state::CompositorMode::Environment => [0.051, 0.055, 0.071, 1.0].into(),
        crate::state::CompositorMode::Mode        => [0.031, 0.031, 0.047, 1.0].into(),
    };

    if backend.bind().is_err() { return; }
    let renderer = backend.renderer();

    let full_rect = Rectangle::from_loc_and_size(
        Point::from((0, 0)),
        output_size.to_logical(1).to_physical(1),
    );

    // Clear background
    if let Err(e) = renderer.clear(bg, &[full_rect]) {
        debug!("Clear error: {:?}", e);
    }

    // Render space elements
    let elements: Vec<CmRenderElement> = state.space.render_elements(
        renderer,
        (0, 0).into(),
        scale,
        1.0,
    );
    let _ = draw_render_elements(renderer, 1.0, &elements, &[full_rect]);

    // Software cursor
    let _ = state.input.pointer_location;  // used for cursor pos

    // Submit frame
    if let Err(e) = backend.submit(None) {
        debug!("Frame submit error: {:?}", e);
        return;
    }

    // Frame callbacks
    let now = state.clock.now();
    for window in state.space.elements() {
        window.send_frame(
            &output, now, Some(std::time::Duration::ZERO),
            |_, _| Some(output.clone()),
        );
    }
}

/// DRM backend rendering (smithay 0.7)
pub fn render_drm_frame(
    state: &mut CmState,
    renderer: &mut GlesRenderer,
    output: &Output,
) {
    let output_size = output.current_mode()
        .map(|m| m.size)
        .unwrap_or_else(|| (1920, 1080).into());
    let scale = Scale::from(output.current_scale().fractional_scale());

    let bg: smithay::backend::renderer::Color32F = [0.051, 0.055, 0.071, 1.0].into();
    let full_rect = Rectangle::from_loc_and_size(
        Point::from((0, 0)),
        output_size.to_logical(1).to_physical(1),
    );

    let _ = renderer.clear(bg, &[full_rect]);

    let elements: Vec<CmRenderElement> = state.space.render_elements(
        renderer, (0, 0).into(), scale, 1.0,
    );
    let _ = draw_render_elements(renderer, 1.0, &elements, &[full_rect]);

    let now = state.clock.now();
    for window in state.space.elements() {
        window.send_frame(
            output, now, Some(std::time::Duration::ZERO),
            |_, _| Some(output.clone()),
        );
    }
}
