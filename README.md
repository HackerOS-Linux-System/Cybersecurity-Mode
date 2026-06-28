# CM — Cybersecurity Mode v0.2

**HackerOS Cybersecurity Mode** — Red Team Edition  
One binary (`cm`). Pure Rust + Slint + Smithay.

---

## Build

```bash
cargo build --release
cp target/release/cm /usr/bin/cm
```

## Commands

```
cm please           → floating app in current Wayland/X session
cm back mode        → switch to tty3 → CM Mode (Red Team)
cm back environment → switch to tty2 → CM Environment (full DE)
cm environment      → full desktop environment with own Wayland compositor
cm mode             → Red Team tool suite with own compositor
cm app settings     → CM Settings app (Slint)
cm app about        → About System app
cm app emoji-picker → Emoji picker with wl-clipboard copy
cm app calculator   → Calculator (evalexpr backend)
cm app containers   → Container manager (podman/docker/distrobox)
cm app clipboard    → CM clipboard manager (replaces Klipper)
cm status           → system, container & dependency status
cm version          → version info
```

## Stack

| Component | Technology |
|-----------|-----------|
| Language | Rust (100%) |
| UI | Slint 1.5 |
| Compositor | Smithay 0.3 + XWayland |
| Config | hk-parser 0.3 (.hk format) |
| Desktop entries | freedesktop_entry_parser 2.x |
| DBus | zbus 4 |
| Calculator | evalexpr 11 |
| Clipboard | wl-clipboard (wl-copy/wl-paste) |

## Config (.hk format)

Location: `~/.config/hackeros/Cybersecurity-Mode/cm.hk`

```hk
! CM Configuration — hk-parser 0.3 format
! Syntax: [section] -> key => value

[environment]
-> default_wallpaper => /usr/share/wallpapers/HackerOS-Wallpapers/Wallpaper23.png
-> icon_theme => BeautyLine
-> launcher_icon => /usr/share/HackerOS/ICONS/HackerOS-Cybersecurity.png
-> default_system_monitor => stacer

[compositor]
-> enable_xwayland => true
-> enable_animations => true

[container]
-> name => cybersec-mode-env
-> engine => podman
-> image => blackarchlinux/blackarch
-> shell => hsh

[keybindings]
-> launcher => Super
-> terminal => Super+Return
-> close_window => Alt+F4
-> maximize => Super+Up
-> tile_left => Super+Left
-> tile_right => Super+Right
-> screenshot => Print
-> lock_screen => Super+L
```

## CM Environment

**Single unified taskbar at bottom.** No top bar. No separate panels.  
Everything in one 40px bar: launcher icon | workspace dots | open windows | tray | clock | settings | power.

### Default Apps
| Role | App |
|------|-----|
| Terminal | Hacker Term (**external binary** — not implemented in CM) |
| File Manager | nemo |
| Text Editor | kate |
| Browser | mullvad-browser |
| System Monitor | **stacer** |
| Clipboard | **CM own** (cm app clipboard, replaces Klipper) |
| Screenshots | spectacle (wlr-screencopy) |
| Documents | papers |
| Image Viewer | loupe |
| Media Player | haruna |
| Email | thunderbird |
| Partitions | kde-partition-manager |

### Icon Themes
- **Default:** BeautyLine (KDE)
- **Fallback chain:** breeze → hicolor → Adwaita → gnome → pixmaps
- `index.theme` parsed with freedesktop_entry_parser 2.x

### Launcher
- Custom icon: `/usr/share/HackerOS/ICONS/HackerOS-Cybersecurity.png`
- Scans all `.desktop` files via freedesktop_entry_parser 2.x
- `OnlyShowIn` / `NotShowIn` / `NoDisplay` / `Hidden` respected

### Compositor (Smithay)
- DRM/KMS for TTY (libseat session)
- Winit backend for nested/testing
- XWayland with full `XwmHandler` (map/unmap/configure/maximize/fullscreen/minimize)
- wlr-layer-shell (taskbar anchoring)
- wlr-foreign-toplevel-management (window list for taskbar)
- wlr-screencopy-unstable-v1 (Spectacle screenshots)
- wp-viewporter + wp-fractional-scale
- xdg-shell (Wayland windows)
- Keyboard: Super+Return/Alt+F4/Super+Up/Super+L/Super+Left/Super+Right/Print...
- Workspace switching: Super+Page_Down / Super+Page_Up

### Lock Screen
`Super+L` → swaylock → swaylock-effects → gtklock → CM built-in Slint lock screen → wlopm off

### Startup Animation
`play_startup_animation()` → mpv → gst-launch-1.0 → ffplay → skip

## CM Mode — Red Team Tool Store

**50+ tools** with full metadata: install status, difficulty, long description, run/install buttons.

**Install:** Click "Install" → `pacman -S <package>` inside BlackArch container via IPC.  
**Run:** Click "▶" → `container::exec` via podman/docker.

### Categories
Reconnaissance · Web Application · Exploitation · Password Attacks ·
Network · Wireless · Forensics · Post-Exploitation · Social Engineering ·
Vulnerability Analysis · Evasion

## CM Environment Apps (Slint + Rust)

| App | Description |
|-----|-------------|
| Settings | Appearance, display, default apps, workspaces, keybindings, power |
| About System | Hardware/software info (sysinfo crate, pacman count) |
| Emoji Picker | Full emoji DB, search, categories, recent 30, wl-clipboard copy |
| Calculator | Full calculator with evalexpr backend, history |
| Container Manager | podman/docker/distrobox — BoxBuddy equivalent |
| Clipboard Manager | CM own — 200 entry history, pin, search, wl-clipboard |

## What remains for production release

1. **Slint dynamic images** — `@image-url(runtime_path)` needs Slint 1.5 dynamic image feature
2. **DRM mode enumeration** — enumerate real display modes (edid) instead of hardcoded 1920x1080  
3. **Hardware cursor plane** — DRM cursor plane for zero-copy cursor rendering
4. **wlr-screencopy buffer blit** — actually copy framebuffer to SHM buffer for Spectacle
5. **PAM authentication** — built-in lock screen password verification
6. **Compositor workspace animation** — slide/fade transition (render two workspace buffers)
7. **Foreign toplevel → taskbar** — send window add/remove/focus events via IPC to shell
8. **DBus NotificationClosed signal** — emit signal on dismiss/timeout
9. **Notification model rebuild** — fix Slint model update in env/mod.rs notification consumer
10. **Verify hk-parser 0.3 API** — confirm `as_map()`, `as_string()`, `as_bool()`, `as_number()` method names match published crate

## License

BSD-3-Clause © 2026 HackerOS Team
