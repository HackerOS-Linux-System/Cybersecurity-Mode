use anyhow::Result;
use crate::hk_parser::{load_hk_file, write_hk_file};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tracing::{info, warn};

fn hk_str(cfg: &crate::hk_parser::HkConfig, section: &str, key: &str, default: &str) -> String {
    cfg.get(section)
        .and_then(|s| s.as_map().ok())
        .and_then(|m| m.get(key))
        .and_then(|v| v.as_string().ok())
        .unwrap_or_else(|| default.to_string())
}

fn hk_bool(cfg: &crate::hk_parser::HkConfig, section: &str, key: &str, default: bool) -> bool {
    cfg.get(section)
        .and_then(|s| s.as_map().ok())
        .and_then(|m| m.get(key))
        .and_then(|v| v.as_bool().ok())
        .unwrap_or(default)
}

fn hk_u32(cfg: &crate::hk_parser::HkConfig, section: &str, key: &str, default: u32) -> u32 {
    cfg.get(section)
        .and_then(|s| s.as_map().ok())
        .and_then(|m| m.get(key))
        .and_then(|v| v.as_number().ok())
        .map(|f| f as u32)
        .unwrap_or(default)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CmTheme {
    pub name:         String,
    pub display_name: String,
    pub author:       String,
    pub version:      String,

    pub bg_primary:    String,
    pub bg_secondary:  String,
    pub bg_tertiary:   String,
    pub bg_panel:      String,
    pub bg_card:       String,

    pub border:        String,
    pub border_focus:  String,
    pub border_active: String,

    pub text_primary:   String,
    pub text_secondary: String,
    pub text_muted:     String,

    pub accent:        String,
    pub accent_hover:  String,
    pub accent_text:   String,

    pub success: String,
    pub warning: String,
    pub danger:  String,
    pub info:    String,

    pub taskbar_bg:     String,
    pub taskbar_height: u32,

    pub window_border_radius: u32,
    pub window_shadow:        bool,
    pub window_shadow_blur:   u32,

    pub blur_enabled:      bool,
    pub blur_radius:       u32,
    pub enable_animations: bool,
    pub animation_ms:      u32,

    pub wallpaper: Option<String>,
}

impl Default for CmTheme {
    fn default() -> Self {
        Self {
            name:         "cybersec-dark".into(),
            display_name: "Cybersec Dark".into(),
            author:       "HackerOS Team".into(),
            version:      "0.2".into(),

            bg_primary:   "#0d0e12".into(),
            bg_secondary: "#13141a".into(),
            bg_tertiary:  "#0a0b0f".into(),
            bg_panel:     "#111218".into(),
            bg_card:      "#161720".into(),

            border:        "#1e2030".into(),
            border_focus:  "#3a4060".into(),
            border_active: "#ef4444".into(),

            text_primary:   "#e8e9f0".into(),
            text_secondary: "#9098b0".into(),
            text_muted:     "#505870".into(),

            accent:       "#ef4444".into(),
            accent_hover: "#dc2626".into(),
            accent_text:  "#ffffff".into(),

            success: "#22c55e".into(),
            warning: "#f59e0b".into(),
            danger:  "#ef4444".into(),
            info:    "#3b82f6".into(),

            taskbar_bg:     "#0a0b0f".into(),
            taskbar_height: 40,

            window_border_radius: 8,
            window_shadow:        true,
            window_shadow_blur:   24,

            blur_enabled:      true,
            blur_radius:       12,
            enable_animations: true,
            animation_ms:      200,

            wallpaper: None,
        }
    }
}

impl CmTheme {
    /// Load from /usr/share/themes/<name>/config.hk
    pub fn load(name: &str) -> Result<Self> {
        let path = PathBuf::from(format!("/usr/share/themes/{}/config.hk", name));
        if !path.exists() {
            warn!("Theme '{}' not found at {:?}, using default", name, path);
            return Ok(Self::default());
        }

        let hk = load_hk_file(&path)?;
        let mut t = Self::default();
        t.name = name.to_string();

        t.display_name = hk_str(&hk, "meta", "display_name", &t.display_name);
        t.author       = hk_str(&hk, "meta", "author",       &t.author);
        t.version      = hk_str(&hk, "meta", "version",      &t.version);

        t.bg_primary    = hk_str(&hk, "colors", "bg_primary",   &t.bg_primary);
        t.bg_secondary  = hk_str(&hk, "colors", "bg_secondary", &t.bg_secondary);
        t.bg_tertiary   = hk_str(&hk, "colors", "bg_tertiary",  &t.bg_tertiary);
        t.bg_panel      = hk_str(&hk, "colors", "bg_panel",     &t.bg_panel);
        t.bg_card       = hk_str(&hk, "colors", "bg_card",      &t.bg_card);
        t.border        = hk_str(&hk, "colors", "border",       &t.border);
        t.border_focus  = hk_str(&hk, "colors", "border_focus", &t.border_focus);
        t.border_active = hk_str(&hk, "colors", "border_active",&t.border_active);
        t.text_primary  = hk_str(&hk, "colors", "text_primary", &t.text_primary);
        t.text_secondary= hk_str(&hk, "colors", "text_secondary",&t.text_secondary);
        t.text_muted    = hk_str(&hk, "colors", "text_muted",   &t.text_muted);
        t.accent        = hk_str(&hk, "colors", "accent",       &t.accent);
        t.accent_hover  = hk_str(&hk, "colors", "accent_hover", &t.accent_hover);
        t.success       = hk_str(&hk, "colors", "success",      &t.success);
        t.warning       = hk_str(&hk, "colors", "warning",      &t.warning);
        t.danger        = hk_str(&hk, "colors", "danger",       &t.danger);
        t.info          = hk_str(&hk, "colors", "info",         &t.info);

        t.taskbar_bg     = hk_str(&hk, "taskbar", "bg",     &t.taskbar_bg);
        t.taskbar_height = hk_u32(&hk, "taskbar", "height", t.taskbar_height);

        t.window_border_radius = hk_u32(&hk,  "windows", "border_radius", t.window_border_radius);
        t.window_shadow        = hk_bool(&hk, "windows", "shadow",        t.window_shadow);
        t.window_shadow_blur   = hk_u32(&hk,  "windows", "shadow_blur",   t.window_shadow_blur);

        t.blur_enabled      = hk_bool(&hk, "effects", "blur_enabled",      t.blur_enabled);
        t.blur_radius       = hk_u32(&hk,  "effects", "blur_radius",       t.blur_radius);
        t.enable_animations = hk_bool(&hk, "effects", "enable_animations", t.enable_animations);
        t.animation_ms      = hk_u32(&hk,  "effects", "animation_ms",      t.animation_ms);

        let wp = hk_str(&hk, "wallpaper", "path", "");
        if !wp.is_empty() { t.wallpaper = Some(wp); }

        info!("Loaded theme '{}' ({})", t.display_name, name);
        Ok(t)
    }

    pub fn list_available() -> Vec<String> {
        let mut themes = vec!["cybersec-dark".to_string()];
        if let Ok(entries) = std::fs::read_dir("/usr/share/themes") {
            for e in entries.flatten() {
                if e.path().join("config.hk").exists() {
                    if let Some(n) = e.file_name().to_str() {
                        let n = n.to_string();
                        if !themes.contains(&n) { themes.push(n); }
                    }
                }
            }
        }
        themes
    }
}
