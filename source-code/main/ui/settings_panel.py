from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QCheckBox, QLineEdit,
    QSpinBox, QSlider, QGroupBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal


class SettingRow(QWidget):
    """Single settings row: label + control."""
    def __init__(self, label: str, control: QWidget, hint: str = ""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        col = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #e8e8e8; font-size: 13px; font-weight: 500;")
        col.addWidget(lbl)
        if hint:
            lbl_hint = QLabel(hint)
            lbl_hint.setStyleSheet("color: #555; font-size: 11px;")
            col.addWidget(lbl_hint)
        layout.addLayout(col)
        layout.addStretch()
        layout.addWidget(control)


class SectionHeader(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(
            "color: #666; font-size: 10px; font-weight: 700; "
            "letter-spacing: 2px; padding: 16px 0 8px;"
        )


class Divider(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet("background: #2e2e2e; max-height: 1px; margin: 4px 0;")


class SettingsPanel(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, config, theme_manager):
        super().__init__()
        self._config = config
        self._theme  = theme_manager
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(56)
        hdr.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #2e2e2e;")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(24, 0, 24, 0)
        lbl = QLabel("Settings")
        lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #e8e8e8;")
        hdr_l.addWidget(lbl)
        outer.addWidget(hdr)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 8, 32, 32)
        layout.setSpacing(0)

        # ── Appearance ────────────────────────────────────────────────────
        layout.addWidget(SectionHeader("APPEARANCE"))

        self._cmb_theme = QComboBox()
        self._cmb_theme.addItems(["dark_gray", "dark_black", "dark_slate", "light"])
        self._cmb_theme.setCurrentText(self._config.get("theme", "dark_gray"))
        self._cmb_theme.setFixedWidth(180)
        self._cmb_theme.currentTextChanged.connect(self._on_theme_change)
        layout.addWidget(SettingRow("Theme", self._cmb_theme, "Visual color theme"))

        layout.addWidget(Divider())

        self._spn_font = QSpinBox()
        self._spn_font.setRange(9, 24)
        self._spn_font.setValue(self._config.get("font_size", 13))
        self._spn_font.setFixedWidth(80)
        self._spn_font.valueChanged.connect(lambda v: self._config.set("font_size", v))
        layout.addWidget(SettingRow("UI Font Size", self._spn_font))

        layout.addWidget(Divider())

        self._spn_term_font = QSpinBox()
        self._spn_term_font.setRange(9, 24)
        self._spn_term_font.setValue(self._config.get("terminal_font_size", 13))
        self._spn_term_font.setFixedWidth(80)
        self._spn_term_font.valueChanged.connect(lambda v: self._config.set("terminal_font_size", v))
        layout.addWidget(SettingRow("Terminal Font Size", self._spn_term_font))

        # ── Mode ──────────────────────────────────────────────────────────
        layout.addWidget(SectionHeader("OPERATIONAL MODE"))

        self._chk_always_ask = QCheckBox()
        self._chk_always_ask.setChecked(self._config.get("always_ask_mode", True))
        self._chk_always_ask.toggled.connect(lambda v: self._config.set("always_ask_mode", v))
        layout.addWidget(SettingRow(
            "Always ask mode at startup",
            self._chk_always_ask,
            "Show mode selection dialog when Cybersecurity Mode starts"
        ))

        # ── Container ─────────────────────────────────────────────────────
        layout.addWidget(SectionHeader("CONTAINER"))

        self._cmb_engine = QComboBox()
        self._cmb_engine.addItems(["podman", "docker"])
        self._cmb_engine.setCurrentText(self._config.get("container_engine", "podman"))
        self._cmb_engine.setFixedWidth(180)
        self._cmb_engine.currentTextChanged.connect(lambda v: self._config.set("container_engine", v))
        layout.addWidget(SettingRow("Container Engine", self._cmb_engine, "podman recommended"))

        layout.addWidget(Divider())

        self._txt_image = QLineEdit(self._config.get("container_image", "blackarchlinux/blackarch"))
        self._txt_image.setFixedWidth(280)
        self._txt_image.editingFinished.connect(
            lambda: self._config.set("container_image", self._txt_image.text())
        )
        layout.addWidget(SettingRow("Container Image", self._txt_image))

        layout.addWidget(Divider())

        self._txt_cname = QLineEdit(self._config.get("container_name", "cybersec-mode-env"))
        self._txt_cname.setFixedWidth(280)
        self._txt_cname.editingFinished.connect(
            lambda: self._config.set("container_name", self._txt_cname.text())
        )
        layout.addWidget(SettingRow("Container Name", self._txt_cname))

        # ── Shell ─────────────────────────────────────────────────────────
        layout.addWidget(SectionHeader("SHELL"))

        self._cmb_shell = QComboBox()
        self._cmb_shell.addItems(["bash", "zsh", "fish", "sh"])
        self._cmb_shell.setCurrentText(self._config.get("shell", "bash"))
        self._cmb_shell.setFixedWidth(180)
        self._cmb_shell.currentTextChanged.connect(lambda v: self._config.set("shell", v))
        layout.addWidget(SettingRow("Default Shell", self._cmb_shell))

        # ── Keybindings ───────────────────────────────────────────────────
        layout.addWidget(SectionHeader("KEYBINDINGS"))

        kb = self._config.get("keybindings", {})
        self._kb_fields = {}
        for action, default in [
            ("toggle_terminal", "Ctrl+T"),
            ("toggle_docs",     "Ctrl+D"),
            ("toggle_main",     "Ctrl+M"),
            ("toggle_settings", "Ctrl+,"),
            ("hacker_menu",     "Ctrl+H"),
        ]:
            txt = QLineEdit(kb.get(action, default))
            txt.setFixedWidth(140)
            txt.editingFinished.connect(lambda v=txt, a=action: self._save_kb(a, v.text()))
            self._kb_fields[action] = txt
            layout.addWidget(SettingRow(action.replace("_", " ").title(), txt))
            layout.addWidget(Divider())

        # ── Logging ───────────────────────────────────────────────────────
        layout.addWidget(SectionHeader("LOGGING"))

        self._cmb_log = QComboBox()
        self._cmb_log.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._cmb_log.setCurrentText(self._config.get("log_level", "INFO"))
        self._cmb_log.setFixedWidth(140)
        self._cmb_log.currentTextChanged.connect(lambda v: self._config.set("log_level", v))
        layout.addWidget(SettingRow("Log Level", self._cmb_log))

        layout.addStretch()

        # Save button
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("btnPrimary")
        btn_save.setFixedHeight(40)
        btn_save.setFixedWidth(180)
        btn_save.clicked.connect(self._save_all)
        layout.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignRight)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _on_theme_change(self, name: str):
        self._config.set("theme", name)
        self.theme_changed.emit(name)

    def _save_kb(self, action: str, value: str):
        kb = self._config.get("keybindings", {})
        kb[action] = value
        self._config.set("keybindings", kb)

    def _save_all(self):
        self._config.save()
