from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QCheckBox, QLineEdit,
    QSpinBox, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.network_widget import NetworkManagerWidget


def _sec_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #444; font-size: 10px; font-weight: 700; "
        "letter-spacing: 2px; padding: 20px 0 6px;"
    )
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background: #1e1e28; max-height: 1px; margin: 2px 0;")
    return f


class SettingRow(QWidget):
    def __init__(self, label: str, control: QWidget, hint: str = ""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        col = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #ccc; font-size: 13px; font-weight: 500;")
        col.addWidget(lbl)
        if hint:
            lh = QLabel(hint)
            lh.setStyleSheet("color: #444; font-size: 11px;")
            col.addWidget(lh)
        layout.addLayout(col)
        layout.addStretch()
        layout.addWidget(control)


class SettingsPanel(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, config, theme_manager):
        super().__init__()
        self._config = config
        self._theme  = theme_manager
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet("background: #0d0d10; border-bottom: 1px solid #1e1e28;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)
        lbl = QLabel("Settings")
        lbl.setStyleSheet("font-size: 17px; font-weight: 700; color: #e8e8f0;")
        hl.addWidget(lbl)
        root.addWidget(hdr)

        # Tab widget for settings categories
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #0d0d10; }
            QTabBar::tab {
                background: transparent; color: #444;
                padding: 10px 18px; font-size: 12px; border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected { color: #ccc; border-bottom-color: #22c55e; }
            QTabBar::tab:hover { color: #999; }
        """)

        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_container_tab(), "Container")
        tabs.addTab(self._build_network_tab(), "Network")
        tabs.addTab(self._build_keys_tab(), "Keybindings")

        root.addWidget(tabs)

    # ── Tabs ──────────────────────────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        page, layout = self._scroll_page()

        layout.addWidget(_sec_header("APPEARANCE"))

        self._cmb_theme = QComboBox()
        self._cmb_theme.addItems(["dark_gray", "dark_black", "dark_slate", "light"])
        self._cmb_theme.setCurrentText(self._config.get("theme", "dark_gray"))
        self._cmb_theme.setFixedWidth(180)
        self._cmb_theme.currentTextChanged.connect(self._on_theme)
        layout.addWidget(SettingRow("Theme", self._cmb_theme, "Visual color scheme"))
        layout.addWidget(_divider())

        self._spn_ui_font = QSpinBox()
        self._spn_ui_font.setRange(9, 24)
        self._spn_ui_font.setValue(self._config.get("font_size", 13))
        self._spn_ui_font.setFixedWidth(80)
        self._spn_ui_font.valueChanged.connect(lambda v: self._config.set("font_size", v))
        layout.addWidget(SettingRow("UI Font Size", self._spn_ui_font))
        layout.addWidget(_divider())

        self._spn_term_font = QSpinBox()
        self._spn_term_font.setRange(9, 24)
        self._spn_term_font.setValue(self._config.get("terminal_font_size", 13))
        self._spn_term_font.setFixedWidth(80)
        self._spn_term_font.valueChanged.connect(lambda v: self._config.set("terminal_font_size", v))
        layout.addWidget(SettingRow("Terminal Font Size", self._spn_term_font))

        layout.addWidget(_sec_header("OPERATIONAL MODE"))

        self._chk_always_ask = QCheckBox()
        self._chk_always_ask.setChecked(self._config.get("always_ask_mode", True))
        self._chk_always_ask.toggled.connect(lambda v: self._config.set("always_ask_mode", v))
        layout.addWidget(SettingRow(
            "Always ask mode at startup",
            self._chk_always_ask,
            "Show Red/Blue mode dialog every time Cybersecurity Mode launches"
        ))

        layout.addWidget(_sec_header("LOGGING"))
        self._cmb_log = QComboBox()
        self._cmb_log.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self._cmb_log.setCurrentText(self._config.get("log_level", "INFO"))
        self._cmb_log.setFixedWidth(140)
        self._cmb_log.currentTextChanged.connect(lambda v: self._config.set("log_level", v))
        layout.addWidget(SettingRow("Log Level", self._cmb_log))

        layout.addStretch()
        layout.addWidget(self._save_btn())
        return page

    def _build_container_tab(self) -> QWidget:
        page, layout = self._scroll_page()

        layout.addWidget(_sec_header("CONTAINER ENGINE"))

        self._cmb_engine = QComboBox()
        self._cmb_engine.addItems(["podman", "docker"])
        self._cmb_engine.setCurrentText(self._config.get("container_engine", "podman"))
        self._cmb_engine.setFixedWidth(180)
        self._cmb_engine.currentTextChanged.connect(
            lambda v: self._config.set("container_engine", v)
        )
        layout.addWidget(SettingRow(
            "Container Engine", self._cmb_engine, "Podman recommended (rootless)"
        ))
        layout.addWidget(_divider())

        self._txt_image = QLineEdit(
            self._config.get("container_image", "blackarchlinux/blackarch")
        )
        self._txt_image.setFixedWidth(300)
        self._txt_image.editingFinished.connect(
            lambda: self._config.set("container_image", self._txt_image.text())
        )
        layout.addWidget(SettingRow("Container Image", self._txt_image))
        layout.addWidget(_divider())

        self._txt_cname = QLineEdit(
            self._config.get("container_name", "cybersec-mode-env")
        )
        self._txt_cname.setFixedWidth(300)
        self._txt_cname.editingFinished.connect(
            lambda: self._config.set("container_name", self._txt_cname.text())
        )
        layout.addWidget(SettingRow("Container Name", self._txt_cname))

        layout.addWidget(_sec_header("SHELL"))
        self._cmb_shell = QComboBox()
        self._cmb_shell.addItems(["hsh", "bash", "zsh", "fish", "sh"])
        self._cmb_shell.setCurrentText(self._config.get("shell", "hsh"))
        self._cmb_shell.setFixedWidth(180)
        self._cmb_shell.currentTextChanged.connect(
            lambda v: self._config.set("shell", v)
        )
        layout.addWidget(SettingRow(
            "Default Shell", self._cmb_shell,
            "hsh = HackerOS native shell  |  bash as fallback"
        ))

        layout.addWidget(_sec_header("CONTAINER ACTIONS"))
        btn_row = QHBoxLayout()
        for label, cmd in [
            ("▶ Start", "container start"),
            ("■ Stop",  "container stop"),
            ("✕ Remove", "container rm"),
        ]:
            b = QPushButton(label)
            b.setFixedHeight(32)
            b.setStyleSheet(
                "QPushButton { background: #111118; border: 1px solid #2a2a38; "
                "color: #888; border-radius: 5px; font-size: 12px; padding: 0 14px; }"
                "QPushButton:hover { background: #1a1a24; color: #ccc; }"
            )
            b.clicked.connect(lambda _, c=cmd: self._run_cybersec_cmd(c))
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Re-run wizard
        layout.addWidget(_divider())
        btn_wizard = QPushButton("↺  Re-run First-Run Wizard")
        btn_wizard.setFixedHeight(34)
        btn_wizard.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #3b82f644; "
            "color: #3b82f6; border-radius: 5px; font-size: 12px; padding: 0 14px; }"
            "QPushButton:hover { background: #3b82f618; }"
        )
        btn_wizard.clicked.connect(self._rerun_wizard)
        layout.addWidget(btn_wizard)

        layout.addStretch()
        layout.addWidget(self._save_btn())
        return page

    def _build_network_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)

        lbl = QLabel(
            "Network Manager (nmcli frontend)\n"
            "Connect to WiFi or Ethernet before pulling the container image."
        )
        lbl.setStyleSheet("color: #555; font-size: 11px; padding-bottom: 6px;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self._net_widget = NetworkManagerWidget()
        layout.addWidget(self._net_widget)

        return page

    def _build_keys_tab(self) -> QWidget:
        page, layout = self._scroll_page()
        layout.addWidget(_sec_header("KEYBINDINGS"))

        kb = self._config.get("keybindings", {})
        self._kb_fields: dict[str, QLineEdit] = {}
        defaults = {
            "toggle_main":     "Ctrl+M",
            "toggle_terminal": "Ctrl+T",
            "toggle_docs":     "Ctrl+D",
            "toggle_settings": "Ctrl+,",
            "hacker_menu":     "Ctrl+H",
        }
        for action, default in defaults.items():
            txt = QLineEdit(kb.get(action, default))
            txt.setFixedWidth(160)
            txt.editingFinished.connect(
                lambda _=None, a=action, t=txt: self._save_kb(a, t.text())
            )
            self._kb_fields[action] = txt
            label = action.replace("_", " ").title()
            layout.addWidget(SettingRow(label, txt))
            layout.addWidget(_divider())

        layout.addStretch()
        layout.addWidget(self._save_btn())
        return page

    # ── Helpers ───────────────────────────────────────────────────────────

    def _scroll_page(self) -> tuple[QWidget, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: #0d0d10; }")

        inner = QWidget()
        inner.setStyleSheet("background: #0d0d10;")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(28, 8, 28, 28)
        layout.setSpacing(0)
        scroll.setWidget(inner)
        return scroll, layout

    def _save_btn(self) -> QPushButton:
        btn = QPushButton("Save Settings")
        btn.setFixedHeight(38)
        btn.setFixedWidth(160)
        btn.setStyleSheet(
            "QPushButton { background: #0a180a; border: 1px solid #22c55e44; "
            "color: #22c55e; font-size: 13px; font-weight: 700; border-radius: 5px; }"
            "QPushButton:hover { background: #22c55e22; }"
        )
        btn.clicked.connect(self._config.save)
        return btn

    def _on_theme(self, name: str):
        self._config.set("theme", name)
        self.theme_changed.emit(name)

    def _save_kb(self, action: str, value: str):
        kb = self._config.get("keybindings", {})
        kb[action] = value
        self._config.set("keybindings", kb)

    def _run_cybersec_cmd(self, subcmd: str):
        import subprocess
        subprocess.Popen(["cybersec"] + subcmd.split())

    def _rerun_wizard(self):
        from ui.first_run_wizard import FirstRunWizard
        from PyQt6.QtWidgets import QDialog
        self._config.set("container_setup_done", "false")
        wiz = FirstRunWizard(self._config, self)
        wiz.exec()
