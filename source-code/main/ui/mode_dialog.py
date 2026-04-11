from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ModeCard(QFrame):
    clicked_sig = pyqtSignal(str)

    def __init__(self, mode: str, icon: str, title: str, desc: str,
                 tools: list[str], color: str):
        super().__init__()
        self._mode  = mode
        self._color = color
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet(f"font-size: 40px;")
        layout.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 800; letter-spacing: 2px;"
        )
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("color: #888; font-size: 12px; line-height: 1.5;")
        layout.addWidget(lbl_desc)

        # Tool tags
        tags_frame = QFrame()
        tags_layout = QVBoxLayout(tags_frame)
        tags_layout.setContentsMargins(0, 8, 0, 0)
        tags_layout.setSpacing(4)
        for tool in tools:
            tag = QLabel(f"▸ {tool}")
            tag.setStyleSheet("color: #666; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
            tags_layout.addWidget(tag)
        layout.addWidget(tags_frame)

        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(
                f"QFrame {{ background: {self._color}18; "
                f"border: 2px solid {self._color}; border-radius: 10px; }}"
            )
        else:
            self.setStyleSheet(
                "QFrame { background: #1e1e1e; border: 2px solid #2e2e2e; border-radius: 10px; }"
            )

    def set_selected(self, v: bool):
        self._selected = v
        self._update_style()

    def mousePressEvent(self, e):
        self.clicked_sig.emit(self._mode)


class ModeSelectionDialog(QDialog):
    def __init__(self, parent, config, force: bool = False):
        super().__init__(parent)
        self._config = config
        self._force  = force
        self._mode   = config.get("mode") or "red"

        self.setWindowTitle("Select Operational Mode")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("""
            QDialog {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 12px;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(20)

        # Header
        lbl_title = QLabel("SELECT OPERATIONAL MODE")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(
            "color: #e8e8e8; font-size: 18px; font-weight: 800; letter-spacing: 3px;"
        )
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Choose your working context for this session")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(lbl_sub)

        # Cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)

        self._card_red = ModeCard(
            "red", "🔴", "RED MODE",
            "Offensive security & penetration testing.\nActive exploitation and vulnerability research.",
            ["nmap", "metasploit", "burpsuite", "sqlmap", "hydra", "aircrack-ng"],
            "#ef4444"
        )
        self._card_blue = ModeCard(
            "blue", "🔵", "BLUE MODE",
            "Defensive security & audit.\nMonitoring, hardening and compliance analysis.",
            ["wireshark", "suricata", "lynis", "openvas", "fail2ban", "auditd"],
            "#3b82f6"
        )

        self._card_red.clicked_sig.connect(self._select_mode)
        self._card_blue.clicked_sig.connect(self._select_mode)

        cards_row.addWidget(self._card_red)
        cards_row.addWidget(self._card_blue)
        layout.addLayout(cards_row)

        # Set initial selection
        self._select_mode(self._mode)

        # Always-ask checkbox (only shown when not forced)
        if not self._force:
            self._chk_always = QCheckBox("Always ask at startup")
            self._chk_always.setChecked(config_val := self._config.get("always_ask_mode", True))
            self._chk_always.setStyleSheet("color: #888; font-size: 12px;")
            layout.addWidget(self._chk_always, alignment=Qt.AlignmentFlag.AlignCenter)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #2e2e2e; max-height: 1px;")
        layout.addWidget(sep)

        # Confirm button
        btn = QPushButton(f"  Enter {self._mode.upper()} MODE  ")
        btn.setObjectName("btnPrimary")
        btn.setFixedHeight(44)
        btn.setStyleSheet(
            f"background: {'#ef4444' if self._mode == 'red' else '#3b82f6'}; "
            "color: white; border: none; border-radius: 6px; "
            "font-size: 14px; font-weight: 700; letter-spacing: 1px;"
        )
        btn.clicked.connect(self._confirm)
        self._btn_confirm = btn
        layout.addWidget(btn)

    def _select_mode(self, mode: str):
        self._mode = mode
        self._card_red.set_selected(mode == "red")
        self._card_blue.set_selected(mode == "blue")
        if hasattr(self, "_btn_confirm"):
            color = "#ef4444" if mode == "red" else "#3b82f6"
            self._btn_confirm.setText(f"  Enter {mode.upper()} MODE  ")
            self._btn_confirm.setStyleSheet(
                f"background: {color}; color: white; border: none; "
                "border-radius: 6px; font-size: 14px; font-weight: 700; letter-spacing: 1px;"
            )

    def _confirm(self):
        self._config.set("mode", self._mode)
        if not self._force and hasattr(self, "_chk_always"):
            self._config.set("always_ask_mode", self._chk_always.isChecked())
        self.accept()
