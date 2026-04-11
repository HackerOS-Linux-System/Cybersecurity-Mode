#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cybersecurity Mode - Main Entry Point
HackerOS Cybersecurity Suite
Python 3.13 + PyQt6
Compiled with Nuitka -> cybersec-mode-main
"""

import sys
import os
import json
import subprocess
import signal
import logging
from pathlib import Path

# ── PyQt6 ──────────────────────────────────────────────────────────────────
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame, QSplitter,
    QDialog, QButtonGroup, QRadioButton, QCheckBox, QMessageBox,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, QProcess, QRect, QPoint
)
from PyQt6.QtGui import (
    QFont, QFontDatabase, QPixmap, QIcon, QColor, QPalette,
    QLinearGradient, QPainter, QPen, QBrush, QAction, QKeySequence,
    QShortcut
)

# ── Internal modules ────────────────────────────────────────────────────────
from ui.theme import ThemeManager
from ui.main_panel import MainPanel
from ui.terminal_panel import TerminalPanel
from ui.docs_panel import DocsPanel
from ui.settings_panel import SettingsPanel
from ui.sidebar import Sidebar
from ui.hacker_menu import HackerMenu
from ui.mode_dialog import ModeSelectionDialog
from ui.titlebar import TitleBar
from core.config import ConfigManager
from core.logger import setup_logger
from core.ipc import IPCClient


# ── Constants ───────────────────────────────────────────────────────────────
APP_NAME        = "Cybersecurity Mode"
APP_VERSION     = "1.0.0"
ORG_NAME        = "HackerOS"
INSTALL_DIR     = Path("/usr/lib/HackerOS/Cybersecurity-Mode")
CACHE_DIR       = Path.home() / ".cache" / "HackerOS" / "Cybersecurity-Mode"
LOG_DIR         = Path.home() / ".local" / "share" / "HackerOS" / "Cybersecurity-Mode" / "logs"
CONFIG_PATH     = CACHE_DIR / "config.json"
ICON_PATH       = Path("/usr/share/HackerOS/ICONS/HackerOS.png")
BACKEND_BIN     = INSTALL_DIR / "cybersec-mode-backend"


def setup_environment():
    """Ensure required directories exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


class CybersecurityModeApp(QMainWindow):
    """Main application window."""

    mode_changed = pyqtSignal(str)   # "red" | "blue"

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config  = config
        self.logger  = logging.getLogger("CybersecMode")
        self.ipc     = IPCClient(BACKEND_BIN)
        self.theme   = ThemeManager(config.get("theme", "dark_gray"))

        self._build_ui()
        self._apply_theme()
        self._connect_signals()
        self._start_backend()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1280, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Load icon
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        # Root widget
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Custom title bar
        self.titlebar = TitleBar(self, APP_NAME, ICON_PATH, self.config)
        root_layout.addWidget(self.titlebar)

        # Body: sidebar + content
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar(self.config)
        body_layout.addWidget(self.sidebar)

        # Stacked content panels
        self.stack = QStackedWidget()
        self.panel_main     = MainPanel(self.config, self.ipc)
        self.panel_terminal = TerminalPanel(self.config)
        self.panel_docs     = DocsPanel(self.config)
        self.panel_settings = SettingsPanel(self.config, self.theme)

        self.stack.addWidget(self.panel_main)       # index 0
        self.stack.addWidget(self.panel_terminal)   # index 1
        self.stack.addWidget(self.panel_docs)       # index 2
        self.stack.addWidget(self.panel_settings)   # index 3

        body_layout.addWidget(self.stack)
        root_layout.addWidget(body)

        # Hacker Menu (bottom-left, overlay)
        self.hacker_menu = HackerMenu(self)
        self.hacker_menu.hide()

        # Status bar
        self._build_statusbar(root_layout)

    def _build_statusbar(self, parent_layout: QVBoxLayout):
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(32)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(12, 0, 12, 0)

        # Hacker Menu button (bottom-left)
        self.btn_hacker_menu = QPushButton("⚡ Hacker Menu")
        self.btn_hacker_menu.setObjectName("hackerMenuBtn")
        self.btn_hacker_menu.setFixedHeight(24)
        bl.addWidget(self.btn_hacker_menu, alignment=Qt.AlignmentFlag.AlignLeft)

        bl.addStretch()

        # Mode indicator
        self.lbl_mode = QLabel()
        self._refresh_mode_label()
        bl.addWidget(self.lbl_mode)

        # Version
        lbl_ver = QLabel(f"v{APP_VERSION}")
        lbl_ver.setObjectName("versionLabel")
        bl.addWidget(lbl_ver)

        parent_layout.addWidget(bar)

    def _refresh_mode_label(self):
        mode = self.config.get("mode", "red")
        color = "#ef4444" if mode == "red" else "#3b82f6"
        icon  = "🔴" if mode == "red" else "🔵"
        self.lbl_mode.setText(f"{icon} {mode.upper()} MODE  |  ")
        self.lbl_mode.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 11px;")

    # ── Theme ──────────────────────────────────────────────────────────────

    def _apply_theme(self):
        self.setStyleSheet(self.theme.generate_stylesheet())

    # ── Signals ────────────────────────────────────────────────────────────

    def _connect_signals(self):
        # Sidebar navigation
        self.sidebar.navigate.connect(self.stack.setCurrentIndex)

        # Hacker menu toggle
        self.btn_hacker_menu.clicked.connect(self._toggle_hacker_menu)

        # Hacker menu actions
        self.hacker_menu.switch_plasma.connect(self._switch_to_plasma)
        self.hacker_menu.restart_app.connect(self._restart_app)
        self.hacker_menu.shutdown_sys.connect(lambda: self._sys_action("poweroff"))
        self.hacker_menu.reboot_sys.connect(lambda: self._sys_action("reboot"))
        self.hacker_menu.update_sys.connect(self._run_update)
        self.hacker_menu.change_mode.connect(self._change_mode)

        # Settings theme change
        self.panel_settings.theme_changed.connect(self._on_theme_changed)

        # Mode change propagation
        self.mode_changed.connect(self.panel_main.on_mode_changed)
        self.mode_changed.connect(self.panel_terminal.on_mode_changed)

        # Title bar
        self.titlebar.close_requested.connect(self.close)
        self.titlebar.minimize_requested.connect(self.showMinimized)
        self.titlebar.maximize_requested.connect(self._toggle_maximize)

    # ── Backend ────────────────────────────────────────────────────────────

    def _start_backend(self):
        if BACKEND_BIN.exists():
            self.ipc.start()
            self.logger.info("Backend IPC started")
        else:
            self.logger.warning(f"Backend binary not found: {BACKEND_BIN}")

    # ── Actions ────────────────────────────────────────────────────────────

    def _toggle_hacker_menu(self):
        if self.hacker_menu.isVisible():
            self.hacker_menu.hide()
        else:
            btn_pos = self.btn_hacker_menu.mapToGlobal(QPoint(0, 0))
            menu_h  = 300
            self.hacker_menu.move(
                btn_pos.x(),
                btn_pos.y() - menu_h - 4
            )
            self.hacker_menu.show()
            self.hacker_menu.raise_()

    def _switch_to_plasma(self):
        is_session = os.environ.get("XDG_SESSION_TYPE") or os.environ.get("CYBERSEC_SESSION")
        if not is_session:
            QMessageBox.warning(self, "Not in session",
                "Switch to Plasma is only available when running as a Cybersecurity Mode session.")
            return
        subprocess.Popen(["startplasma-wayland"])

    def _restart_app(self):
        QApplication.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _sys_action(self, action: str):
        reply = QMessageBox.question(
            self, f"Confirm {action}",
            f"Are you sure you want to {action}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            subprocess.run(["systemctl", action])

    def _run_update(self):
        self.panel_terminal.run_command("cybersec update")
        self.stack.setCurrentIndex(1)
        self.hacker_menu.hide()

    def _change_mode(self):
        self.hacker_menu.hide()
        dlg = ModeSelectionDialog(self, self.config, force=True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_mode_label()
            self.mode_changed.emit(self.config.get("mode", "red"))

    def _on_theme_changed(self, theme_name: str):
        self.theme.set_theme(theme_name)
        self.setStyleSheet(self.theme.generate_stylesheet())

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── Cleanup ────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.ipc.stop()
        self.config.save()
        event.accept()


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    setup_environment()
    logger = setup_logger(LOG_DIR)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    config = ConfigManager(CONFIG_PATH)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Qt6 handles HiDPI automatically — AA_UseHighDpiPixmaps removed in Qt6

    # Mode selection dialog (first run or always_ask)
    always_ask = config.get("always_ask_mode", True)
    mode_set   = config.get("mode") is not None

    if always_ask or not mode_set:
        dlg = ModeSelectionDialog(None, config)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            # User closed dialog without choosing — default red
            config.set("mode", "red")
        config.save()

    window = CybersecurityModeApp(config)
    window.showMaximized()

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
