from __future__ import annotations
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeySequence


class HackerMenu(QFrame):
    switch_plasma = pyqtSignal()
    restart_app   = pyqtSignal()
    shutdown_sys  = pyqtSignal()
    reboot_sys    = pyqtSignal()
    update_sys    = pyqtSignal()
    change_mode   = pyqtSignal()

    ACTIONS = [
        ("🖥  Switch to Plasma",   "switch_plasma",  None),
        ("🔄  Restart App",        "restart_app",    None),
        ("⏻   Shutdown",           "shutdown_sys",   None),
        ("↺   Reboot",             "reboot_sys",     None),
        ("⬆   Update System",      "update_sys",     None),
        ("⇄   Change Mode",        "change_mode",    None),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("hackerMenuPanel")
        self.setFixedWidth(240)
        self.setFixedHeight(310)
        self.setWindowFlags(Qt.WindowType.SubWindow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        lbl = QLabel("⚡ HACKER MENU")
        lbl.setObjectName("hackerMenuTitle")
        layout.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #2e2e2e; max-height: 1px; margin: 4px 0;")
        layout.addWidget(sep)

        for label, sig_name, _ in self.ACTIONS:
            btn = QPushButton(label)
            btn.setObjectName("hackerMenuAction")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(38)
            btn.clicked.connect(getattr(self, sig_name).emit)
            layout.addWidget(btn)

        # Shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)
