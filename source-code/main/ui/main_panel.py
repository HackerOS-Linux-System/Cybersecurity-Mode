from __future__ import annotations
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QLineEdit, QSizePolicy,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QFont


# ── Tool catalog ──────────────────────────────────────────────────────────────

RED_TOOLS = [
    ("nmap",        "Network scanner",              "🔍", "#ef4444"),
    ("metasploit",  "Exploitation framework",       "💉", "#ef4444"),
    ("burpsuite",   "Web proxy & scanner",          "🕷",  "#f97316"),
    ("sqlmap",      "SQL injection automation",     "🗄",  "#f97316"),
    ("hydra",       "Login brute-force",            "🔑", "#eab308"),
    ("aircrack-ng", "WiFi security",                "📡", "#eab308"),
    ("hashcat",     "Password cracking (GPU)",      "🔓", "#ef4444"),
    ("john",        "John the Ripper",              "🔐", "#f97316"),
    ("gobuster",    "Directory/DNS brute-force",    "📂", "#eab308"),
    ("nikto",       "Web server scanner",           "🌐", "#ef4444"),
    ("wireshark",   "Packet analyzer",              "📶", "#3b82f6"),
    ("netcat",      "TCP/IP swiss army knife",      "🔌", "#22c55e"),
]

BLUE_TOOLS = [
    ("wireshark",   "Traffic analysis",             "📶", "#3b82f6"),
    ("suricata",    "IDS/IPS engine",               "🛡",  "#3b82f6"),
    ("lynis",       "Security auditing",            "🔎", "#22c55e"),
    ("openvas",     "Vulnerability scanner",        "🩺", "#3b82f6"),
    ("fail2ban",    "Intrusion prevention",         "🚫", "#22c55e"),
    ("auditd",      "Linux audit daemon",           "📋", "#22c55e"),
    ("clamav",      "Antivirus engine",             "🦠",  "#3b82f6"),
    ("rkhunter",    "Rootkit hunter",               "🔦", "#22c55e"),
    ("ossec",       "HIDS",                         "🏠", "#3b82f6"),
    ("tcpdump",     "Command-line packet analyzer", "📡", "#22c55e"),
    ("nmap",        "Network auditing",             "🔍", "#3b82f6"),
    ("snort",       "IDS/IPS",                      "👃", "#22c55e"),
]


class ToolCard(QFrame):
    def __init__(self, name: str, desc: str, icon: str, color: str, ipc):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(90)
        self._name = name
        self._ipc  = ipc

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        row = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"font-size: 20px;")
        row.addWidget(lbl_icon)

        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700; "
            "font-family: 'JetBrains Mono', monospace;"
        )
        row.addWidget(lbl_name)
        row.addStretch()

        btn_run = QPushButton("▶")
        btn_run.setFixedSize(28, 24)
        btn_run.setStyleSheet(
            f"background: {color}22; border: 1px solid {color}55; "
            f"color: {color}; border-radius: 4px; font-size: 12px;"
        )
        btn_run.clicked.connect(self._launch)
        btn_run.setToolTip(f"Open {name} in terminal")
        row.addWidget(btn_run)
        layout.addLayout(row)

        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(lbl_desc)

    def _launch(self):
        if self._ipc:
            self._ipc.call_async(
                "container_exec",
                {"cmd": self._name},
                lambda _: None
            )


class ContainerStatusWidget(QFrame):
    def __init__(self, ipc):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(80)
        self._ipc = ipc

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        col = QVBoxLayout()
        lbl_title = QLabel("CONTAINER STATUS")
        lbl_title.setObjectName("cardTitle")
        col.addWidget(lbl_title)

        self.lbl_status = QLabel("● Checking…")
        self.lbl_status.setStyleSheet("color: #666; font-size: 12px; font-family: monospace;")
        col.addWidget(self.lbl_status)
        layout.addLayout(col)

        layout.addStretch()

        col2 = QVBoxLayout()
        self.btn_toggle = QPushButton("Start Container")
        self.btn_toggle.setObjectName("btnPrimary")
        self.btn_toggle.setFixedHeight(30)
        self.btn_toggle.clicked.connect(self._toggle)
        col2.addWidget(self.btn_toggle)
        layout.addLayout(col2)

        self._running = False
        QTimer.singleShot(500, self._refresh)

    def _refresh(self):
        if not self._ipc:
            self.lbl_status.setText("● Backend unavailable")
            return
        self._ipc.call_async("container_status", {}, self._on_status)

    def _on_status(self, result):
        if result and result.get("running"):
            self._running = True
            self.lbl_status.setText("● Running  —  blackarch/blackarch")
            self.lbl_status.setStyleSheet("color: #22c55e; font-size: 12px; font-family: monospace;")
            self.btn_toggle.setText("Stop Container")
        else:
            self._running = False
            self.lbl_status.setText("● Stopped")
            self.lbl_status.setStyleSheet("color: #ef4444; font-size: 12px; font-family: monospace;")
            self.btn_toggle.setText("Start Container")

    def _toggle(self):
        if self._running:
            self._ipc.call_async("container_stop", {"name": "cybersec-mode-env"}, lambda _: self._refresh())
        else:
            self._ipc.call_async(
                "container_start",
                {"image": "blackarchlinux/blackarch", "name": "cybersec-mode-env"},
                lambda _: self._refresh()
            )


class MainPanel(QWidget):
    def __init__(self, config, ipc):
        super().__init__()
        self._config = config
        self._ipc    = ipc
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        self._lbl_title = QLabel()
        self._lbl_title.setObjectName("panelTitle")
        self._update_title()
        hdr.addWidget(self._lbl_title)

        hdr.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search tools…")
        self._search.setFixedWidth(220)
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._filter_tools)
        hdr.addWidget(self._search)
        layout.addLayout(hdr)

        # Container status
        self._container_status = ContainerStatusWidget(self._ipc)
        layout.addWidget(self._container_status)

        # Tools grid — scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._tools_container = QWidget()
        self._tools_grid = QGridLayout(self._tools_container)
        self._tools_grid.setSpacing(12)
        self._tools_grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._tools_container)
        layout.addWidget(scroll)

        self._tool_cards: list[ToolCard] = []
        self._populate_tools()

    def _update_title(self):
        mode = self._config.get("mode", "red")
        if mode == "red":
            self._lbl_title.setText("⚔  Offensive / Pentest")
            self._lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ef4444;")
        else:
            self._lbl_title.setText("🛡  Defensive / Audit")
            self._lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #3b82f6;")

    def _populate_tools(self):
        # Clear
        for c in self._tool_cards:
            c.deleteLater()
        self._tool_cards.clear()

        mode  = self._config.get("mode", "red")
        tools = RED_TOOLS if mode == "red" else BLUE_TOOLS
        COLS  = 3

        for i, (name, desc, icon, color) in enumerate(tools):
            card = ToolCard(name, desc, icon, color, self._ipc)
            self._tools_grid.addWidget(card, i // COLS, i % COLS)
            self._tool_cards.append(card)

    def _filter_tools(self, text: str):
        text = text.lower()
        for card in self._tool_cards:
            card.setVisible(text in card._name.lower() if text else True)

    @pyqtSlot(str)
    def on_mode_changed(self, mode: str):
        self._update_title()
        self._populate_tools()
