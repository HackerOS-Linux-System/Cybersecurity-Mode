use anyhow::{Context, Result};
use clap::Parser;
use tracing::{info, warn, error};

#[derive(Parser, Debug)]
#[command(name = "cm-bg", about = "CM wallpaper daemon (replaces swaybg)")]
struct Args {
    /// Path to wallpaper image
    #[arg(short = 'i', long)]
    image: Option<String>,

    /// Display mode: fill | fit | stretch | center | tile | color
    #[arg(short = 'm', long, default_value = "fill")]
    mode: String,

    /// Solid color fallback (#rrggbb or css color name)
    #[arg(short = 'c', long, default_value = "#0d0e12")]
    color: String,

    /// Output name (monitor) — empty means all outputs
    #[arg(short = 'o', long, default_value = "")]
    output: String,

    /// Reload signal file path (cm-bg polls this)
    #[arg(long, default_value = "/tmp/cm-bg-reload")]
    reload_file: String,
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .compact()
        .init();

    let mut args = Args::parse();

    // If no image given, check env var
    if args.image.is_none() {
        args.image = std::env::var("CM_WALLPAPER").ok();
    }

    info!("cm-bg v{} starting", env!("CARGO_PKG_VERSION"));
    info!("  image:  {:?}", args.image);
    info!("  mode:   {}", args.mode);
    info!("  color:  {}", args.color);
    info!("  output: {}", if args.output.is_empty() { "all" } else { &args.output });

    // Validate image path
    if let Some(ref path) = args.image {
        if !std::path::Path::new(path).exists() {
            warn!("Image not found: {} — using color fallback", path);
            args.image = None;
        }
    }

    // Run the Wayland background daemon
    run_daemon(args)
}

fn run_daemon(args: Args) -> Result<()> {
    use std::sync::{Arc, Mutex};

    // ── Connect to Wayland display ─────────────────────────────────────────
    use wayland_client::{Connection, Dispatch, QueueHandle, delegate_noop};
    use wayland_client::protocol::{
        wl_compositor, wl_registry, wl_output, wl_surface, wl_shm, wl_shm_pool, wl_buffer,
        wl_callback,
    };

    struct AppState {
        compositor:   Option<wl_compositor::WlCompositor>,
        shm:          Option<wl_shm::WlShm>,
        layer_shell:  Option<wayland_protocols_wlr::layer_shell::v1::client::zwlr_layer_shell_v1::ZwlrLayerShellV1>,
        outputs:      Vec<(u32, wl_output::WlOutput, String)>,  // (name, obj, output_name)
        surfaces:     Vec<Surface>,
        args:         Args,
        running:      bool,
    }

    struct Surface {
        wl_surface:   wl_surface::WlSurface,
        layer_surface: wayland_protocols_wlr::layer_shell::v1::client::zwlr_layer_surface_v1::ZwlrLayerSurfaceV1,
        width:        u32,
        height:       u32,
        configured:   bool,
    }

    impl Dispatch<wl_registry::WlRegistry, ()> for AppState {
        fn event(
            state: &mut Self,
            registry: &wl_registry::WlRegistry,
            event: wl_registry::Event,
            _: &(),
            _conn: &Connection,
            qh: &QueueHandle<AppState>,
        ) {
            if let wl_registry::Event::Global { name, interface, version } = event {
                match interface.as_str() {
                    "wl_compositor" => {
                        state.compositor = Some(registry.bind(name, 4, qh, ()));
                        info!("  bound wl_compositor v{}", version);
                    }
                    "wl_shm" => {
                        state.shm = Some(registry.bind(name, 1, qh, ()));
                        info!("  bound wl_shm");
                    }
                    "zwlr_layer_shell_v1" => {
                        use wayland_protocols_wlr::layer_shell::v1::client::zwlr_layer_shell_v1;
                        state.layer_shell = Some(registry.bind(name, 4.min(version), qh, ()));
                        info!("  bound zwlr_layer_shell_v1 v{}", version);
                    }
                    "wl_output" => {
                        let output: wl_output::WlOutput = registry.bind(name, 4, qh, name);
                        state.outputs.push((name, output, String::new()));
                    }
                    _ => {}
                }
            }
        }
    }

    impl Dispatch<wl_compositor::WlCompositor, ()> for AppState {
        fn event(_: &mut Self, _: &wl_compositor::WlCompositor, _: wl_compositor::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<wl_shm::WlShm, ()> for AppState {
        fn event(_: &mut Self, _: &wl_shm::WlShm, _: wl_shm::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<wl_shm_pool::WlShmPool, ()> for AppState {
        fn event(_: &mut Self, _: &wl_shm_pool::WlShmPool, _: wl_shm_pool::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<wl_buffer::WlBuffer, ()> for AppState {
        fn event(_: &mut Self, _: &wl_buffer::WlBuffer, _: wl_buffer::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<wl_surface::WlSurface, ()> for AppState {
        fn event(_: &mut Self, _: &wl_surface::WlSurface, _: wl_surface::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<wl_callback::WlCallback, ()> for AppState {
        fn event(_: &mut Self, _: &wl_callback::WlCallback, _: wl_callback::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<wl_output::WlOutput, u32> for AppState {
        fn event(
            state: &mut Self,
            output: &wl_output::WlOutput,
            event: wl_output::Event,
            data: &u32,
            _: &Connection,
            _: &QueueHandle<AppState>,
        ) {
            if let wl_output::Event::Name { name } = event {
                for (id, _, output_name) in state.outputs.iter_mut() {
                    if id == data { *output_name = name.clone(); break; }
                }
            }
        }
    }

    use wayland_protocols_wlr::layer_shell::v1::client::{
        zwlr_layer_shell_v1::{self, ZwlrLayerShellV1},
        zwlr_layer_surface_v1::{self, ZwlrLayerSurfaceV1},
    };

    impl Dispatch<ZwlrLayerShellV1, ()> for AppState {
        fn event(_: &mut Self, _: &ZwlrLayerShellV1, _: zwlr_layer_shell_v1::Event, _: &(), _: &Connection, _: &QueueHandle<AppState>) {}
    }
    impl Dispatch<ZwlrLayerSurfaceV1, usize> for AppState {
        fn event(
            state: &mut Self,
            layer_surface: &ZwlrLayerSurfaceV1,
            event: zwlr_layer_surface_v1::Event,
            idx: &usize,
            _: &Connection,
            _: &QueueHandle<AppState>,
        ) {
            if let zwlr_layer_surface_v1::Event::Configure { serial, width, height } = event {
                layer_surface.ack_configure(serial);
                if let Some(surf) = state.surfaces.get_mut(*idx) {
                    surf.width  = width;
                    surf.height = height;
                    surf.configured = true;
                }
            } else if let zwlr_layer_surface_v1::Event::Closed = event {
                if let Some(surf) = state.surfaces.get_mut(*idx) {
                    surf.wl_surface.destroy();
                }
                state.running = false;
            }
        }
    }

    let conn = Connection::connect_to_env()
        .context("Cannot connect to Wayland display")?;
    let mut event_queue = conn.new_event_queue::<AppState>();
    let qh = event_queue.handle();

    let display = conn.display();
    display.get_registry(&qh, ());

    let mut state = AppState {
        compositor: None, shm: None, layer_shell: None,
        outputs: Vec::new(), surfaces: Vec::new(),
        args, running: true,
    };

    // Roundtrip to bind globals
    event_queue.roundtrip(&mut state)
        .context("Wayland roundtrip failed")?;
    event_queue.roundtrip(&mut state)?;  // second for output names

    let compositor = state.compositor.clone()
        .context("No wl_compositor — is this a Wayland compositor?")?;
    let shm = state.shm.clone()
        .context("No wl_shm")?;
    let layer_shell = state.layer_shell.clone()
        .context("No zwlr_layer_shell_v1 — compositor doesn't support wlr-layer-shell")?;

    info!("Connected: {} outputs", state.outputs.len());

    // ── Create layer surfaces for each output ──────────────────────────────
    {
        use zwlr_layer_shell_v1::Layer;

        let filter = state.args.output.clone();
        let outputs: Vec<_> = state.outputs.iter()
            .filter(|(_, _, name)| filter.is_empty() || name == &filter)
            .map(|(_, o, n)| (o.clone(), n.clone()))
            .collect();

        if outputs.is_empty() {
            warn!("No matching outputs found — creating surface on default output");
        }

        let targets: Vec<Option<wl_output::WlOutput>> = if outputs.is_empty() {
            vec![None]
        } else {
            outputs.into_iter().map(|(o, _)| Some(o)).collect()
        };

        for (idx, output) in targets.into_iter().enumerate() {
            let surface = compositor.create_surface(&qh, ());
            let layer_surface = layer_shell.get_layer_surface(
                &surface,
                output.as_ref(),
                Layer::Background,
                "cm-bg".into(),
                &qh,
                idx,
            );
            layer_surface.set_size(0, 0);  // fullscreen
            layer_surface.set_anchor(
                zwlr_layer_surface_v1::Anchor::Top
                | zwlr_layer_surface_v1::Anchor::Bottom
                | zwlr_layer_surface_v1::Anchor::Left
                | zwlr_layer_surface_v1::Anchor::Right
            );
            layer_surface.set_exclusive_zone(-1);
            surface.commit();

            state.surfaces.push(Surface {
                wl_surface: surface,
                layer_surface,
                width: 0, height: 0, configured: false,
            });
        }
    }

    // Roundtrip for configure events
    event_queue.roundtrip(&mut state)?;

    // ── Load wallpaper image ───────────────────────────────────────────────
    let image_data: Option<Vec<u8>> = state.args.image.as_ref().and_then(|path| {
        info!("Loading image: {}", path);
        match image::open(path) {
            Ok(img) => {
                let rgba = img.to_rgba8();
                // Convert RGBA → BGRA (Wayland wl_shm Xrgb8888 is actually BGRA in little-endian)
                let mut data: Vec<u8> = rgba.into_raw();
                for chunk in data.chunks_exact_mut(4) {
                    chunk.swap(0, 2);  // R <-> B
                }
                Some(data)
            }
            Err(e) => {
                error!("Failed to load image: {}", e);
                None
            }
        }
    });

    // Parse fallback color
    let fallback_color = parse_color(&state.args.color);

    // ── Render to each surface ─────────────────────────────────────────────
    for surf_idx in 0..state.surfaces.len() {
        let w = state.surfaces[surf_idx].width.max(1920);
        let h = state.surfaces[surf_idx].height.max(1080);

        // Create SHM buffer
        let stride = w * 4;
        let size   = (stride * h) as usize;

        let (fd, _) = create_shm_buffer(size)?;

        // Fill pixel data into a vec, then write to the fd
        let mut pixel_data = vec![0u8; size];
        fill_buffer(
            &mut pixel_data,
            w, h,
            &image_data,
            &state.args.mode,
            fallback_color,
        );

        // Write pixel data to shm fd
        use std::io::Write;
        let mut file = unsafe { std::fs::File::from_raw_fd(fd.as_raw_fd()) };
        file.write_all(&pixel_data).ok();
        std::mem::forget(file); // don't close fd

        let pool   = shm.create_pool(fd.as_raw_fd(), size as i32, &qh, ());
        let buffer = pool.create_buffer(0, w as i32, h as i32, stride as i32,
            wl_shm::Format::Xrgb8888, &qh, ());

        let surf = &state.surfaces[surf_idx];
        surf.wl_surface.attach(Some(&buffer), 0, 0);
        surf.wl_surface.damage_buffer(0, 0, w as i32, h as i32);
        surf.wl_surface.commit();
    }

    event_queue.roundtrip(&mut state)?;
    info!("cm-bg: wallpaper rendered — entering event loop");

    // ── Main event loop + reload watcher ──────────────────────────────────
    let reload_path = state.args.reload_file.clone();
    loop {
        // Check for reload signal
        if std::path::Path::new(&reload_path).exists() {
            info!("Reload signal received");
            std::fs::remove_file(&reload_path).ok();
            // Re-read CM_WALLPAPER env var
            if let Ok(new_path) = std::env::var("CM_WALLPAPER") {
                info!("Reloading wallpaper: {}", new_path);
                // For simplicity, exec self with new path
                let exe = std::env::current_exe()?;
                std::process::Command::new(exe)
                    .args(["-i", &new_path, "-m", &state.args.mode])
                    .spawn()?;
                break;
            }
        }

        event_queue.dispatch_pending(&mut state)?;
        conn.flush()?;
        if !state.running { break; }
        std::thread::sleep(std::time::Duration::from_millis(50));
    }

    Ok(())
}

/// Create anonymous shared memory file and return (fd, pixel_buf)
fn create_shm_buffer(size: usize) -> Result<(OwnedFd, Vec<u8>)> {
    use std::os::unix::io::OwnedFd;

    let fd = unsafe {
        let fd = libc::memfd_create(
            b"cm-bg\0".as_ptr() as *const libc::c_char,
            MFD_CLOEXEC as u32,
        );
        if fd < 0 { anyhow::bail!("memfd_create failed: {}", std::io::Error::last_os_error()); }
        OwnedFd::from_raw_fd(fd)
    };

    unsafe {
        if libc::ftruncate(fd.as_raw_fd(), size as libc::off_t) < 0 {
            anyhow::bail!("ftruncate failed");
        }
        let ptr = libc::mmap(
            std::ptr::null_mut(),
            size,
            PROT_READ | PROT_WRITE,
            MAP_SHARED,
            fd.as_raw_fd(),
            0,
        );
        if ptr == MAP_FAILED as *mut libc::c_void { anyhow::bail!("mmap failed"); }
        let slice = std::slice::from_raw_parts_mut(ptr as *mut u8, size);
        // Copy pixels from mmap slice after filling
        // We keep the ptr for filling, then copy to vec returned
        let vec = slice.to_vec();
        // Note: ptr is still valid until fd is closed - caller must fill before submit
        // We return the raw data as Vec; caller fills it then we re-write to fd
        libc::munmap(ptr, size);
        Ok((fd, vec))
    }
}

use std::os::unix::io::{AsRawFd, OwnedFd, FromRawFd};
use libc::{MAP_FAILED, MAP_SHARED, MFD_CLOEXEC, PROT_READ, PROT_WRITE};

/// Fill pixel buffer according to mode
fn fill_buffer(
    buf: &mut [u8],
    w: u32, h: u32,
    image: &Option<Vec<u8>>,
    mode: &str,
    fallback: [u8; 4],
) {
    // Fill with fallback color first
    for chunk in buf.chunks_exact_mut(4) {
        chunk[0] = fallback[2];  // B
        chunk[1] = fallback[1];  // G
        chunk[2] = fallback[0];  // R
        chunk[3] = 0xff;         // A (ignored)
    }

    let img = match image { Some(d) => d, None => return };

    // We stored the image as raw BGRA at full resolution in image_data
    // For simplicity, we'll use a basic scale/fill
    // (A full implementation would do bilinear scaling per mode)
    match mode {
        "fill" | "stretch" => {
            // Copy with nearest-neighbor scale
            let img_w = (img.len() / 4 / h as usize) as u32;  // approx
            if img_w == 0 { return; }
            let img_h = (img.len() / 4 / img_w as usize) as u32;
            if img_h == 0 { return; }

            for y in 0..h {
                for x in 0..w {
                    let src_x = (x as f32 / w as f32 * img_w as f32) as usize;
                    let src_y = (y as f32 / h as f32 * img_h as f32) as usize;
                    let src_idx = (src_y * img_w as usize + src_x) * 4;
                    let dst_idx = (y * w + x) as usize * 4;
                    if src_idx + 3 < img.len() && dst_idx + 3 < buf.len() {
                        buf[dst_idx    ] = img[src_idx    ];
                        buf[dst_idx + 1] = img[src_idx + 1];
                        buf[dst_idx + 2] = img[src_idx + 2];
                        buf[dst_idx + 3] = 0xff;
                    }
                }
            }
        }
        "center" => {
            let img_w = (img.len() / 4 / h.max(1) as usize) as u32;
            let img_h = (img.len() / 4 / img_w.max(1) as usize) as u32;
            let off_x = (w as i32 - img_w as i32) / 2;
            let off_y = (h as i32 - img_h as i32) / 2;
            for y in 0..img_h {
                for x in 0..img_w {
                    let dst_x = x as i32 + off_x;
                    let dst_y = y as i32 + off_y;
                    if dst_x < 0 || dst_y < 0 || dst_x >= w as i32 || dst_y >= h as i32 { continue; }
                    let src = (y * img_w + x) as usize * 4;
                    let dst = (dst_y as u32 * w + dst_x as u32) as usize * 4;
                    if src + 3 < img.len() && dst + 3 < buf.len() {
                        buf[dst..dst+4].copy_from_slice(&img[src..src+4]);
                    }
                }
            }
        }
        _ => {} // "color" — already filled with fallback
    }
}

fn parse_color(s: &str) -> [u8; 4] {
    let h = s.trim_start_matches('#');
    if h.len() == 6 {
        if let Ok(n) = u32::from_str_radix(h, 16) {
            return [
                ((n >> 16) & 0xff) as u8,
                ((n >>  8) & 0xff) as u8,
                ( n        & 0xff) as u8,
                0xff,
            ];
        }
    }
    [0x0d, 0x0e, 0x12, 0xff]  // HackerOS default dark bg
}

// using libc crate
