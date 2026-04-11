from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class ColorPalette:
    bg_primary:    str   # main background
    bg_secondary:  str   # panel/card background
    bg_tertiary:   str   # sidebar, statusbar
    bg_hover:      str
    bg_active:     str
    border:        str
    border_active: str
    text_primary:  str
    text_secondary:str
    text_muted:    str
    accent_red:    str   # red mode
    accent_blue:   str   # blue mode
    accent_green:  str   # success
    accent_orange: str   # warning
    accent_yellow: str   # caution
    scrollbar:     str
    input_bg:      str
    selection:     str


PALETTES: Dict[str, ColorPalette] = {
    "dark_gray": ColorPalette(
        bg_primary    = "#1a1a1a",
        bg_secondary  = "#222222",
        bg_tertiary   = "#181818",
        bg_hover      = "#2a2a2a",
        bg_active     = "#333333",
        border        = "#2e2e2e",
        border_active = "#444444",
        text_primary  = "#e8e8e8",
        text_secondary= "#aaaaaa",
        text_muted    = "#666666",
        accent_red    = "#ef4444",
        accent_blue   = "#3b82f6",
        accent_green  = "#22c55e",
        accent_orange = "#f97316",
        accent_yellow = "#eab308",
        scrollbar     = "#333333",
        input_bg      = "#252525",
        selection     = "#3b82f630",
    ),
    "dark_black": ColorPalette(
        bg_primary    = "#0d0d0d",
        bg_secondary  = "#141414",
        bg_tertiary   = "#0a0a0a",
        bg_hover      = "#1e1e1e",
        bg_active     = "#252525",
        border        = "#1e1e1e",
        border_active = "#333333",
        text_primary  = "#f0f0f0",
        text_secondary= "#999999",
        text_muted    = "#555555",
        accent_red    = "#ff3333",
        accent_blue   = "#2563eb",
        accent_green  = "#16a34a",
        accent_orange = "#ea580c",
        accent_yellow = "#ca8a04",
        scrollbar     = "#222222",
        input_bg      = "#161616",
        selection     = "#2563eb30",
    ),
    "dark_slate": ColorPalette(
        bg_primary    = "#0f172a",
        bg_secondary  = "#1e293b",
        bg_tertiary   = "#0d1526",
        bg_hover      = "#263347",
        bg_active     = "#334155",
        border        = "#1e293b",
        border_active = "#475569",
        text_primary  = "#e2e8f0",
        text_secondary= "#94a3b8",
        text_muted    = "#475569",
        accent_red    = "#f43f5e",
        accent_blue   = "#38bdf8",
        accent_green  = "#34d399",
        accent_orange = "#fb923c",
        accent_yellow = "#fbbf24",
        scrollbar     = "#1e293b",
        input_bg      = "#162032",
        selection     = "#38bdf830",
    ),
    "light": ColorPalette(
        bg_primary    = "#f4f4f5",
        bg_secondary  = "#ffffff",
        bg_tertiary   = "#e4e4e7",
        bg_hover      = "#e9e9eb",
        bg_active     = "#d4d4d8",
        border        = "#d4d4d8",
        border_active = "#a1a1aa",
        text_primary  = "#18181b",
        text_secondary= "#52525b",
        text_muted    = "#a1a1aa",
        accent_red    = "#dc2626",
        accent_blue   = "#2563eb",
        accent_green  = "#16a34a",
        accent_orange = "#ea580c",
        accent_yellow = "#b45309",
        scrollbar     = "#d4d4d8",
        input_bg      = "#ffffff",
        selection     = "#2563eb20",
    ),
}

FONT_MONO = "JetBrains Mono, Fira Code, Cascadia Code, monospace"
FONT_UI   = "Inter, IBM Plex Sans, Segoe UI, sans-serif"


class ThemeManager:
    def __init__(self, name: str = "dark_gray"):
        self._name = name if name in PALETTES else "dark_gray"

    @property
    def name(self) -> str:
        return self._name

    @property
    def palette(self) -> ColorPalette:
        return PALETTES[self._name]

    def set_theme(self, name: str):
        if name in PALETTES:
            self._name = name

    def generate_stylesheet(self) -> str:
        p = self.palette
        return f"""
/* ── Global ──────────────────────────────────────────────────────────── */
* {{
    font-family: {FONT_UI};
    outline: none;
}}

QMainWindow, QWidget {{
    background-color: {p.bg_primary};
    color: {p.text_primary};
}}

/* ── TitleBar ────────────────────────────────────────────────────────── */
#titleBar {{
    background-color: {p.bg_tertiary};
    border-bottom: 1px solid {p.border};
    min-height: 40px;
    max-height: 40px;
}}
#titleBarLogo {{
    margin: 0 8px;
}}
#titleBarTitle {{
    color: {p.text_primary};
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
}}
#titleBarBtn {{
    background: transparent;
    border: none;
    color: {p.text_secondary};
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 14px;
}}
#titleBarBtn:hover {{
    background: {p.bg_hover};
    color: {p.text_primary};
}}
#titleBarBtnClose:hover {{
    background: {p.accent_red};
    color: white;
}}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
#sidebar {{
    background-color: {p.bg_tertiary};
    border-right: 1px solid {p.border};
    min-width: 200px;
    max-width: 200px;
}}
#sidebarBtn {{
    background: transparent;
    border: none;
    color: {p.text_secondary};
    text-align: left;
    padding: 12px 20px;
    font-size: 13px;
    font-weight: 500;
    border-radius: 0;
}}
#sidebarBtn:hover {{
    background: {p.bg_hover};
    color: {p.text_primary};
}}
#sidebarBtn[active="true"] {{
    background: {p.bg_active};
    color: {p.text_primary};
    border-left: 3px solid {p.accent_red};
}}
#sidebarSeparator {{
    background: {p.border};
    max-height: 1px;
    margin: 4px 16px;
}}
#sidebarVersion {{
    color: {p.text_muted};
    font-size: 10px;
    padding: 4px 20px;
}}

/* ── Status Bar ──────────────────────────────────────────────────────── */
#statusBar {{
    background-color: {p.bg_tertiary};
    border-top: 1px solid {p.border};
}}
#hackerMenuBtn {{
    background: transparent;
    border: 1px solid {p.border};
    color: {p.accent_green};
    font-size: 11px;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 3px;
    letter-spacing: 0.5px;
}}
#hackerMenuBtn:hover {{
    background: {p.bg_hover};
    border-color: {p.accent_green};
}}
#versionLabel {{
    color: {p.text_muted};
    font-size: 10px;
}}

/* ── Cards / Panels ──────────────────────────────────────────────────── */
#card {{
    background-color: {p.bg_secondary};
    border: 1px solid {p.border};
    border-radius: 6px;
    padding: 16px;
}}
#cardTitle {{
    color: {p.text_primary};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
#panelTitle {{
    color: {p.text_primary};
    font-size: 18px;
    font-weight: 700;
}}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {p.bg_active};
    color: {p.text_primary};
    border: 1px solid {p.border};
    padding: 7px 16px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {p.bg_hover};
    border-color: {p.border_active};
}}
QPushButton:pressed {{
    background-color: {p.bg_secondary};
}}
#btnPrimary {{
    background-color: {p.accent_red};
    border: none;
    color: white;
    font-weight: 700;
}}
#btnPrimary:hover {{
    background-color: #dc2626;
}}
#btnPrimaryBlue {{
    background-color: {p.accent_blue};
    border: none;
    color: white;
    font-weight: 700;
}}
#btnPrimaryBlue:hover {{
    background-color: #2563eb;
}}
#btnDanger {{
    background-color: transparent;
    border: 1px solid {p.accent_red};
    color: {p.accent_red};
}}
#btnDanger:hover {{
    background-color: {p.accent_red};
    color: white;
}}

/* ── Terminal ────────────────────────────────────────────────────────── */
#terminal {{
    background-color: #0a0a0a;
    color: #00ff88;
    font-family: {FONT_MONO};
    font-size: 13px;
    border: 1px solid {p.border};
    border-radius: 4px;
    padding: 8px;
}}
#terminalInput {{
    background-color: #0a0a0a;
    color: #00ff88;
    font-family: {FONT_MONO};
    font-size: 13px;
    border: none;
    border-top: 1px solid {p.border};
    padding: 6px 10px;
}}

/* ── Inputs ──────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {p.input_bg};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {p.border_active};
}}

/* ── Combo / Spin ────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {p.input_bg};
    color: {p.text_primary};
    border: 1px solid {p.border};
    border-radius: 4px;
    padding: 5px 10px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {p.bg_secondary};
    color: {p.text_primary};
    selection-background-color: {p.bg_active};
    border: 1px solid {p.border};
}}

/* ── Scroll ──────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p.scrollbar};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {p.scrollbar};
    border-radius: 3px;
}}

/* ── Tab ─────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {p.border};
    border-radius: 4px;
}}
QTabBar::tab {{
    background: {p.bg_tertiary};
    color: {p.text_secondary};
    padding: 8px 16px;
    border: 1px solid transparent;
    border-bottom: none;
}}
QTabBar::tab:selected {{
    background: {p.bg_secondary};
    color: {p.text_primary};
    border-color: {p.border};
}}

/* ── Separators ──────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {p.border};
    width: 1px;
    height: 1px;
}}

/* ── CheckBox / Radio ────────────────────────────────────────────────── */
QCheckBox, QRadioButton {{
    color: {p.text_primary};
    spacing: 8px;
    font-size: 13px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {p.border_active};
    border-radius: 3px;
    background: {p.input_bg};
}}
QCheckBox::indicator:checked {{
    background: {p.accent_blue};
    border-color: {p.accent_blue};
}}
QRadioButton::indicator {{ border-radius: 8px; }}
QRadioButton::indicator:checked {{
    background: {p.accent_blue};
    border-color: {p.accent_blue};
}}

/* ── Progress ────────────────────────────────────────────────────────── */
QProgressBar {{
    background: {p.bg_active};
    border: 1px solid {p.border};
    border-radius: 4px;
    text-align: center;
    font-size: 11px;
    color: {p.text_primary};
    max-height: 16px;
}}
QProgressBar::chunk {{
    background: {p.accent_green};
    border-radius: 3px;
}}

/* ── Hacker Menu ─────────────────────────────────────────────────────── */
#hackerMenuPanel {{
    background-color: {p.bg_tertiary};
    border: 1px solid {p.border_active};
    border-radius: 8px;
}}
#hackerMenuTitle {{
    color: {p.accent_green};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 10px 16px 4px;
}}
#hackerMenuAction {{
    background: transparent;
    border: none;
    color: {p.text_primary};
    text-align: left;
    padding: 9px 16px;
    font-size: 13px;
    width: 100%;
}}
#hackerMenuAction:hover {{
    background: {p.bg_hover};
}}

/* ── Mode Dialog ─────────────────────────────────────────────────────── */
#modeDialog {{
    background-color: {p.bg_secondary};
    border: 1px solid {p.border};
    border-radius: 8px;
}}
#modeCard {{
    border: 2px solid {p.border};
    border-radius: 8px;
    padding: 20px;
    min-width: 200px;
}}
#modeCardRed:hover, #modeCardRed[selected="true"] {{
    border-color: {p.accent_red};
    background: {p.accent_red}18;
}}
#modeCardBlue:hover, #modeCardBlue[selected="true"] {{
    border-color: {p.accent_blue};
    background: {p.accent_blue}18;
}}

/* ── Label helpers ───────────────────────────────────────────────────── */
.tag {{
    background: {p.bg_active};
    color: {p.text_secondary};
    border-radius: 3px;
    padding: 2px 8px;
    font-size: 11px;
}}
"""
