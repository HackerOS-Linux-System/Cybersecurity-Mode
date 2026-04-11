from __future__ import annotations
from pathlib import Path

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QMouseEvent


class TitleBar(QFrame):
    close_requested    = pyqtSignal()
    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()

    def __init__(self, parent, title: str, icon_path: Path, config):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self._config   = config
        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        # Left: icon + title + mode badge
        if icon_path.exists():
            lbl_icon = QLabel()
            lbl_icon.setObjectName("titleBarLogo")
            pix = QPixmap(str(icon_path)).scaled(
                24, 24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            lbl_icon.setPixmap(pix)
            layout.addWidget(lbl_icon)

        lbl_title = QLabel(title.upper())
        lbl_title.setObjectName("titleBarTitle")
        layout.addWidget(lbl_title)

        self.lbl_mode = QLabel()
        self._set_mode_badge()
        layout.addWidget(self.lbl_mode)

        layout.addStretch()

        # Right: window controls (right-top per spec: logo already top-right via titlebar right section)
        # Actually logo goes to top-right per spec — add it there
        if icon_path.exists():
            lbl_logo_right = QLabel()
            pix2 = QPixmap(str(icon_path)).scaled(
                28, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            lbl_logo_right.setPixmap(pix2)
            lbl_logo_right.setToolTip("HackerOS — Cybersecurity Mode")
            layout.addWidget(lbl_logo_right)

        for sym, name, sig in [
            ("─", "min",   self.minimize_requested),
            ("□", "max",   self.maximize_requested),
            ("✕", "close", self.close_requested),
        ]:
            btn = QPushButton(sym)
            btn.setObjectName("titleBarBtn" + ("Close" if name == "close" else ""))
            if name != "close":
                btn.setObjectName("titleBarBtn")
            btn.setFixedSize(32, 28)
            btn.clicked.connect(sig.emit)
            layout.addWidget(btn)

    def _set_mode_badge(self):
        mode  = self._config.get("mode", "red")
        color = "#ef4444" if mode == "red" else "#3b82f6"
        label = "RED" if mode == "red" else "BLUE"
        self.lbl_mode.setText(f"● {label}")
        self.lbl_mode.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 700; "
            f"background: {color}22; padding: 2px 8px; border-radius: 3px;"
        )

    def refresh_mode(self):
        self._set_mode_badge()

    # ── Drag to move ──────────────────────────────────────────────────────

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.window().move(self.window().pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        self.maximize_requested.emit()
