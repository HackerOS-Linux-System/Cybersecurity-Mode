use smithay::{
    backend::input::{
        AbsolutePositionEvent, Axis, AxisSource, ButtonState, Event, InputEvent,
        KeyState, KeyboardKeyEvent, PointerAxisEvent, PointerButtonEvent,
        PointerMotionEvent, PointerMotionAbsoluteEvent,
    },
    desktop::Window,
    input::{
        keyboard::{keysyms as Keysyms, FilterResult, ModifiersState},
        pointer::{AxisFrame, ButtonEvent, MotionEvent},
    },
    utils::{Logical, Point, SERIAL_COUNTER},
};
use tracing::debug;

use crate::state::CmState;

pub struct InputState {
    pub pointer_location: Point<f64, Logical>,
}

impl InputState {
    pub fn new() -> Self {
        Self { pointer_location: (0.0, 0.0).into() }
    }
}

pub fn process_input_event<B>(state: &mut CmState, event: InputEvent<B>)
where B: smithay::backend::input::InputBackend,
{
    match event {
        InputEvent::Keyboard { event }              => handle_keyboard(state, event),
        InputEvent::PointerMotion { event }         => handle_pointer_motion(state, event),
        InputEvent::PointerMotionAbsolute { event } => handle_pointer_abs(state, event),
        InputEvent::PointerButton { event }         => handle_pointer_button(state, event),
        InputEvent::PointerAxis { event }           => handle_pointer_axis(state, event),
        _ => {}
    }
}

fn handle_keyboard<B: smithay::backend::input::InputBackend>(
    state: &mut CmState,
    event: B::KeyboardKeyEvent,
) {
    let serial = SERIAL_COUNTER.next_serial();
    let time   = Event::time_msec(&event);
    let code   = event.key_code();
    let key_st = event.state();

    let kb = match state.seat.get_keyboard() { Some(k) => k, None => return };

    kb.input::<(), _>(state, code, key_st, serial, time, |state, mods, keysym| {
        if key_st != KeyState::Pressed { return FilterResult::Forward; }

        let sym = keysym.modified_sym();

        // ── Super+Return → terminal ─────────────────────────────────
        if mods.logo && sym == Keysyms::KEY_Return {
            let term = state.config.mode;
            tokio::spawn(async move {
                let _ = tokio::process::Command::new(
                    "/usr/share/HackerOS/Scripts/HackerOS-Apps/Hacker-Term"
                ).spawn();
            });
            return FilterResult::Intercept(());
        }

        // ── Alt+F4 → close focused window ───────────────────────────
        if mods.alt && sym == Keysyms::KEY_F4 {
            if let Some(window) = state.space.elements().next_back().cloned() {
                if let Some(toplevel) = window.toplevel() {
                    toplevel.send_close();
                }
                if let Some(x11) = window.x11_surface() {
                    x11.close().ok();
                }
            }
            return FilterResult::Intercept(());
        }

        // ── Super+Up → maximize focused ─────────────────────────────
        if mods.logo && sym == Keysyms::KEY_Up {
            if let Some(window) = state.space.elements().next_back().cloned() {
                if let Some(toplevel) = window.toplevel() {
                    toplevel.with_pending_state(|s| {
                        s.states.set(smithay::wayland::shell::xdg::ToplevelStateSet::Maximized);
                    });
                    toplevel.send_configure();
                }
            }
            return FilterResult::Intercept(());
        }

        // ── Super+Left → tile left ──────────────────────────────────
        if mods.logo && sym == Keysyms::KEY_Left {
            tile_focused_window(state, TileDir::Left);
            return FilterResult::Intercept(());
        }

        // ── Super+Right → tile right ────────────────────────────────
        if mods.logo && sym == Keysyms::KEY_Right {
            tile_focused_window(state, TileDir::Right);
            return FilterResult::Intercept(());
        }

        // ── Super+Page_Down / Next → workspace next ─────────────────
        if mods.logo && (sym == Keysyms::KEY_Next || sym == Keysyms::KEY_Page_Down) {
            let next = (state.active_workspace + 1) % state.config.workspace_count;
            state.switch_workspace(next);
            return FilterResult::Intercept(());
        }

        // ── Super+Page_Up / Prior → workspace prev ──────────────────
        if mods.logo && (sym == Keysyms::KEY_Prior || sym == Keysyms::KEY_Page_Up) {
            let prev = if state.active_workspace == 0 {
                state.config.workspace_count - 1
            } else {
                state.active_workspace - 1
            };
            state.switch_workspace(prev);
            return FilterResult::Intercept(());
        }

        // ── Super+L → lock screen ───────────────────────────────────
        if mods.logo && sym == Keysyms::KEY_l {
            tokio::spawn(async move {
                crate::environment::lockscreen::lock().await.ok();
            });
            return FilterResult::Intercept(());
        }

        // ── Print → screenshot via Spectacle ───────────────────────
        if sym == Keysyms::KEY_Print {
            let with_region = mods.shift;
            tokio::spawn(async move {
                let mut args = vec![];
                if with_region { args.push("-r"); }
                tokio::process::Command::new("spectacle")
                    .args(&args)
                    .spawn()
                    .ok();
            });
            return FilterResult::Intercept(());
        }

        // ── Super+D → show desktop (minimize all) ──────────────────
        if mods.logo && sym == Keysyms::KEY_d {
            let windows: Vec<_> = state.space.elements().cloned().collect();
            for w in windows {
                state.space.unmap_elem(&w);
            }
            return FilterResult::Intercept(());
        }

        // ── Super+E → file manager ──────────────────────────────────
        if mods.logo && sym == Keysyms::KEY_e {
            tokio::spawn(async move {
                tokio::process::Command::new("nemo").spawn().ok();
            });
            return FilterResult::Intercept(());
        }

        // ── Ctrl+Alt+Backspace → exit compositor ────────────────────
        if mods.ctrl && mods.alt && sym == Keysyms::KEY_BackSpace {
            state.exit();
            return FilterResult::Intercept(());
        }

        FilterResult::Forward
    });
}

enum TileDir { Left, Right }

fn tile_focused_window(state: &mut CmState, dir: TileDir) {
    let window = match state.space.elements().next_back().cloned() {
        Some(w) => w,
        None => return,
    };

    let output_size = state.output_size;
    let taskbar_h   = state.config.taskbar_height as i32;
    let usable_h    = output_size.h - taskbar_h;

    let (x, y, w, h) = match dir {
        TileDir::Left  => (0, 0, output_size.w / 2, usable_h),
        TileDir::Right => (output_size.w / 2, 0, output_size.w / 2, usable_h),
    };

    if let Some(toplevel) = window.toplevel() {
        toplevel.with_pending_state(|s| {
            s.size = Some((w, h).into());
        });
        toplevel.send_configure();
    }
    state.space.map_element(window, (x, y), true);
}

fn handle_pointer_motion<B: smithay::backend::input::InputBackend>(
    state: &mut CmState, event: B::PointerMotionEvent,
) {
    let delta = event.delta();
    state.input.pointer_location.x =
        (state.input.pointer_location.x + delta.x).clamp(0.0, state.output_size.w as f64);
    state.input.pointer_location.y =
        (state.input.pointer_location.y + delta.y).clamp(0.0, state.output_size.h as f64);
    update_pointer_focus(state);
}

fn handle_pointer_abs<B: smithay::backend::input::InputBackend>(
    state: &mut CmState, event: B::PointerMotionAbsoluteEvent,
) {
    state.input.pointer_location = event.position_transformed(state.output_size);
    update_pointer_focus(state);
}

fn update_pointer_focus(state: &mut CmState) {
    let loc    = state.input.pointer_location;
    let serial = SERIAL_COUNTER.next_serial();

    let under = state.space.element_under(loc).map(|(w, p)| (w.clone(), p));

    if let Some(ptr) = state.seat.get_pointer() {
        let focus = under.as_ref().and_then(|(w, p)| {
            w.wl_surface().map(|s| (s, *p))
        });
        ptr.motion(state, focus, &MotionEvent { location: loc, serial, time: 0 });
    }
}

fn handle_pointer_button<B: smithay::backend::input::InputBackend>(
    state: &mut CmState, event: B::PointerButtonEvent,
) {
    let serial = SERIAL_COUNTER.next_serial();
    let button = event.button_code();
    let btn_st = event.state();

    if btn_st == ButtonState::Pressed {
        let loc = state.input.pointer_location;
        if let Some((window, _)) = state.space.element_under(loc) {
            let window = window.clone();
            state.space.raise_element(&window, true);
            if let Some(kb) = state.seat.get_keyboard() {
                let surf = window.wl_surface().map(|s| s.clone());
                kb.set_focus(state, surf, serial);
            }
        }
    }

    if let Some(ptr) = state.seat.get_pointer() {
        ptr.button(state, &ButtonEvent {
            button: button,
            state: btn_st,
            serial,
            time: event.time_msec(),
        });
    }
}

fn handle_pointer_axis<B: smithay::backend::input::InputBackend>(
    state: &mut CmState, event: B::PointerAxisEvent,
) {
    if let Some(ptr) = state.seat.get_pointer() {
        let mut frame = AxisFrame::new(event.time_msec()).source(event.source());
        if let Some(h) = event.amount(Axis::Horizontal) {
            if h != 0.0 { frame = frame.value(Axis::Horizontal, h); }
        }
        if let Some(v) = event.amount(Axis::Vertical) {
            if v != 0.0 { frame = frame.value(Axis::Vertical, v); }
        }
        ptr.axis(state, frame);
    }
}
