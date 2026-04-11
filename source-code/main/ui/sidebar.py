from __future__ import annotations
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt


NAV_ITEMS = [
    ("⚔",  "Main",      0),
    ("⬛",  "Terminal",  1),
    ("📖",  "Docs",      2),
    ("⚙",  "Settings",  3),
]


class Sidebar(QFrame):
    navigate = pyqtSignal(int)

    def __init__(self, config):
        super().__init__()
        self.setObjectName("sidebar")
        self._config  = config
        self._buttons = []
        self._current = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        # Section label
        lbl = QLabel("NAVIGATION")
        lbl.setObjectName("sidebarVersion")
        lbl.setStyleSheet("color: #555; font-size: 9px; letter-spacing: 2px; padding: 8px 20px 4px;")
        layout.addWidget(lbl)

        for icon, name, idx in NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setObjectName("sidebarBtn")
            btn.setCheckable(False)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _, i=idx: self._on_nav(i))
            layout.addWidget(btn)
            self._buttons.append(btn)

        sep = QFrame()
        sep.setObjectName("sidebarSeparator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        layout.addStretch()

        # Mode badge
        mode  = config.get("mode", "red")
        color = "#ef4444" if mode == "red" else "#3b82f6"
        lbl_mode = QLabel(f"● {'RED MODE' if mode == 'red' else 'BLUE MODE'}")
        lbl_mode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_mode.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; "
            f"padding: 8px; letter-spacing: 1px;"
        )
        layout.addWidget(lbl_mode)
        self._lbl_mode = lbl_mode

        self._update_active(0)

    def _on_nav(self, idx: int):
        self._update_active(idx)
        self.navigate.emit(idx)

    def _update_active(self, idx: int):
        self._current = idx
        mode  = self._config.get("mode", "red")
        color = "#ef4444" if mode == "red" else "#3b82f6"
        for i, btn in enumerate(self._buttons):
            if i == idx:
                btn.setStyleSheet(
                    f"background: #2a2a2a; color: #e8e8e8; "
                    f"border-left: 3px solid {color}; "
                    f"text-align: left; padding: 12px 20px; "
                    f"font-size: 13px; font-weight: 600;"
                )
            else:
                btn.setStyleSheet(
                    "background: transparent; color: #888; "
                    "border: none; text-align: left; "
                    "padding: 12px 20px; font-size: 13px;"
                )

    def on_mode_changed(self, mode: str):
        color = "#ef4444" if mode == "red" else "#3b82f6"
        label = "RED MODE" if mode == "red" else "BLUE MODE"
        self._lbl_mode.setText(f"● {label}")
        self._lbl_mode.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; "
            f"padding: 8px; letter-spacing: 1px;"
        )
        self._update_active(self._current)
