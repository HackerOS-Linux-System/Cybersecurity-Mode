use smithay::{
    backend::renderer::{
        element::surface::WaylandSurfaceRenderElement,
        gles::GlesRenderer,
        Renderer, Texture,
    },
    output::Output,
    reexports::wayland_server::{
        protocol::wl_shm,
        Client, DataInit, Dispatch, DisplayHandle, GlobalDispatch, New, Resource,
    },
    utils::{Logical, Physical, Rectangle, Scale, Transform},
    wayland::shm::ShmState,
};
use tracing::{debug, info, warn};

use crate::state::CmState;

// wlr-screencopy protocol objects
// These are defined in wayland-protocols-wlr
use wayland_protocols_wlr::screencopy::v1::server::{
    zwlr_screencopy_frame_v1::{self, ZwlrScreencopyFrameV1},
    zwlr_screencopy_manager_v1::{self, ZwlrScreencopyManagerV1},
};

pub struct ScreencopyManagerState;
pub struct ScreencopyFrame {
    pub output: Output,
    pub region: Option<Rectangle<i32, Logical>>,
    pub with_cursor: bool,
}

impl ScreencopyManagerState {
    pub fn new(display: &DisplayHandle) -> Self {
        display.create_global::<CmState, ZwlrScreencopyManagerV1, _>(3, ());
        Self
    }
}

impl GlobalDispatch<ZwlrScreencopyManagerV1, ()> for CmState {
    fn bind(
        _state: &mut CmState,
        _handle: &DisplayHandle,
        _client: &Client,
        resource: New<ZwlrScreencopyManagerV1>,
        _global_data: &(),
        data_init: &mut DataInit<'_, CmState>,
    ) {
        data_init.init(resource, ());
    }
}

impl Dispatch<ZwlrScreencopyManagerV1, ()> for CmState {
    fn request(
        state: &mut CmState,
        _client: &Client,
        _manager: &ZwlrScreencopyManagerV1,
        request: zwlr_screencopy_manager_v1::Request,
        _data: &(),
        _display: &DisplayHandle,
        data_init: &mut DataInit<'_, CmState>,
    ) {
        match request {
            zwlr_screencopy_manager_v1::Request::CaptureOutput {
                frame,
                overlay_cursor,
                output,
            } => {
                let output = state.space.outputs()
                    .find(|o| o.owns(&output))
                    .cloned();

                if let Some(output) = output {
                    let frame_obj = data_init.init(frame, ScreencopyFrame {
                        output: output.clone(),
                        region: None,
                        with_cursor: overlay_cursor != 0,
                    });

                    // Send buffer info to client
                    let size = output.current_mode()
                        .map(|m| m.size)
                        .unwrap_or((1920, 1080).into());

                    frame_obj.buffer(
                        wl_shm::Format::Xbgr8888,
                        size.w as u32,
                        size.h as u32,
                        size.w as u32 * 4,
                    );
                    frame_obj.ready(0, 0, 0); // simplified
                    info!("Screencopy: captured output {}x{}", size.w, size.h);
                }
            }

            zwlr_screencopy_manager_v1::Request::CaptureOutputRegion {
                frame,
                overlay_cursor,
                output,
                x, y, width, height,
            } => {
                let output = state.space.outputs()
                    .find(|o| o.owns(&output))
                    .cloned();

                if let Some(output) = output {
                    let region = Rectangle::from_loc_and_size((x, y), (width, height));
                    let frame_obj = data_init.init(frame, ScreencopyFrame {
                        output,
                        region: Some(region),
                        with_cursor: overlay_cursor != 0,
                    });
                    frame_obj.buffer(
                        wl_shm::Format::Xbgr8888,
                        width as u32, height as u32,
                        width as u32 * 4,
                    );
                    frame_obj.ready(0, 0, 0);
                    info!("Screencopy: captured region {}x{} at ({},{})", width, height, x, y);
                }
            }

            zwlr_screencopy_manager_v1::Request::Destroy => {}
            _ => warn!("Unhandled screencopy manager request"),
        }
    }
}

impl Dispatch<ZwlrScreencopyFrameV1, ScreencopyFrame> for CmState {
    fn request(
        _state: &mut CmState,
        _client: &Client,
        _frame: &ZwlrScreencopyFrameV1,
        request: zwlr_screencopy_frame_v1::Request,
        _data: &ScreencopyFrame,
        _display: &DisplayHandle,
        _data_init: &mut DataInit<'_, CmState>,
    ) {
        match request {
            zwlr_screencopy_frame_v1::Request::Copy { buffer: _ } => {
                debug!("Screencopy: copy request");
                // Full implementation would blit the framebuffer into the SHM buffer
            }
            zwlr_screencopy_frame_v1::Request::CopyWithDamage { buffer: _ } => {
                debug!("Screencopy: copy with damage request");
            }
            zwlr_screencopy_frame_v1::Request::Destroy => {}
            _ => {}
        }
    }
}
