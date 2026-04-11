from __future__ import annotations

import os
import shutil
import subprocess
import threading
import urllib.request
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QWidget, QProgressBar, QTextEdit,
    QSizePolicy, QCheckBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon

# ── constants ────────────────────────────────────────────────────────────────

CONTAINER_IMAGE = "blackarchlinux/blackarch"
CONTAINER_NAME  = "cybersec-mode-env"
TEST_URL        = "https://archlinux.org"
ICON_PATH       = Path("/usr/share/HackerOS/ICONS/HackerOS.png")

TOOL_SET_RED = [
    "nmap", "masscan", "gobuster", "feroxbuster", "sqlmap", "nikto",
    "hydra", "hashcat", "john", "aircrack-ng", "metasploit",
    "burpsuite", "wireshark-cli", "netcat", "impacket", "responder",
]
TOOL_SET_BLUE = [
    "suricata", "lynis", "rkhunter", "chkrootkit", "fail2ban",
    "auditd", "clamav", "openvas", "aide", "tcpdump",
]

STYLE = """
QDialog { background: #0d0d10; border: 1px solid #2a2a36; border-radius: 10px; }
QLabel  { color: #c8c8d8; font-family: 'IBM Plex Sans', sans-serif; }
QTextEdit {
    background: #060608; color: #22e87a;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    border: 1px solid #1a1a24; border-radius: 5px; padding: 6px;
}
QProgressBar {
    background: #111118; border: 1px solid #1e1e2a; border-radius: 4px;
    height: 6px; text-align: center; color: transparent;
}
QProgressBar::chunk { background: #22c55e; border-radius: 3px; }
QPushButton {
    background: #1a1a24; border: 1px solid #2e2e3e; color: #ccc;
    border-radius: 5px; padding: 8px 18px; font-size: 13px;
}
QPushButton:hover { background: #222230; border-color: #44444e; color: #fff; }
QPushButton#primary {
    background: #1a3a1a; border-color: #22c55e55; color: #22c55e; font-weight: 700;
}
QPushButton#primary:hover { background: #22c55e22; }
QPushButton#danger  {
    background: #2a1a1a; border-color: #ef444455; color: #ef4444; font-weight: 700;
}
"""


# ── workers ──────────────────────────────────────────────────────────────────

class NetCheckWorker(QThread):
    result = pyqtSignal(bool)   # True = has internet
    def run(self):
        try:
            urllib.request.urlopen(TEST_URL, timeout=4)
            self.result.emit(True)
        except Exception:
            self.result.emit(False)


class ContainerCheckWorker(QThread):
    result = pyqtSignal(bool, str)  # (running_or_exists, state_str)
    def __init__(self, engine: str):
        super().__init__()
        self._engine = engine

    def run(self):
        try:
            out = subprocess.run(
                [self._engine, "inspect", "--format", "{{.State.Status}}", CONTAINER_NAME],
                capture_output=True, text=True, timeout=5
            )
            state = out.stdout.strip()
            if out.returncode == 0 and state:
                self.result.emit(True, state)
            else:
                self.result.emit(False, "not found")
        except Exception:
            self.result.emit(False, "error")


class ContainerSetupWorker(QThread):
    log_line  = pyqtSignal(str)
    progress  = pyqtSignal(int)
    finished  = pyqtSignal(bool, str)   # success, message

    def __init__(self, engine: str, install_tools: bool):
        super().__init__()
        self._engine        = engine
        self._install_tools = install_tools

    def run(self):
        steps = [
            ("pull",    f"Pulling {CONTAINER_IMAGE}…",             self._pull),
            ("create",  "Creating container…",                    self._create),
            ("keyring", "Updating BlackArch keyring…",            self._keyring),
            ("update",  "Upgrading packages…",                    self._update),
        ]
        if self._install_tools:
            steps.append(("tools", "Installing security tools…", self._tools))

        total = len(steps)
        for i, (_, label, fn) in enumerate(steps):
            self.log_line.emit(f"\n[{i+1}/{total}] {label}")
            ok, msg = fn()
            self.progress.emit(int((i + 1) / total * 100))
            if not ok:
                self.finished.emit(False, msg)
                return
            self.log_line.emit(f"  ✓ done")

        self.finished.emit(True, "Container ready!")

    def _run_cmd(self, cmd: list[str]) -> tuple[bool, str]:
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace"
            )
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                if line:
                    self.log_line.emit("  " + line)
            proc.wait()
            return proc.returncode == 0, ""
        except FileNotFoundError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def _pull(self):
        return self._run_cmd([self._engine, "pull", CONTAINER_IMAGE])

    def _create(self):
        # Check if already exists
        existing = subprocess.run(
            [self._engine, "inspect", CONTAINER_NAME],
            capture_output=True
        ).returncode == 0

        if existing:
            self.log_line.emit("  Container already exists — starting…")
            return self._run_cmd([self._engine, "start", CONTAINER_NAME])

        return self._run_cmd([
            self._engine, "run", "-d",
            "--name",          CONTAINER_NAME,
            "--privileged",
            "--network",       "host",
            "--security-opt",  "seccomp=unconfined",
            "--cap-add",       "NET_ADMIN",
            "--cap-add",       "NET_RAW",
            "--cap-add",       "SYS_PTRACE",
            "--cap-add",       "SYS_ADMIN",
            "-v",              "/home:/home:rw",
            "-v",              "/tmp/cybersec:/tmp/cybersec:rw",
            "-v",              "/etc/resolv.conf:/etc/resolv.conf:ro",
            CONTAINER_IMAGE,
            "sleep", "infinity",
        ])

    def _keyring(self):
        script = (
            "pacman-key --init 2>/dev/null; "
            "pacman-key --populate archlinux blackarch 2>/dev/null; "
            "pacman -Sy --noconfirm blackarch-keyring 2>/dev/null || true"
        )
        return self._run_cmd([self._engine, "exec", CONTAINER_NAME, "bash", "-c", script])

    def _update(self):
        return self._run_cmd([
            self._engine, "exec", CONTAINER_NAME,
            "bash", "-c", "pacman -Syu --noconfirm 2>/dev/null"
        ])

    def _tools(self):
        tools = " ".join(TOOL_SET_RED + TOOL_SET_BLUE)
        script = f"pacman -S --noconfirm {tools} 2>/dev/null || true"
        return self._run_cmd([self._engine, "exec", CONTAINER_NAME, "bash", "-c", script])


# ── pages ────────────────────────────────────────────────────────────────────

class WelcomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(16)

        if ICON_PATH.exists():
            lbl_icon = QLabel()
            pix = QPixmap(str(ICON_PATH)).scaled(
                72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            lbl_icon.setPixmap(pix)
            lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_icon)

        lbl_title = QLabel("Cybersecurity Mode")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(
            "color: #e8e8f0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;"
        )
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("v0.1  —  HackerOS")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color: #444; font-size: 13px; font-family: monospace;")
        layout.addWidget(lbl_sub)

        layout.addSpacing(10)

        for icon, text in [
            ("📦", "This wizard will set up your BlackArch Linux security container."),
            ("🔧", "All security tools run inside an isolated Podman container."),
            ("🌐", "An internet connection is required to pull the container image."),
            ("⚡", "Setup takes 5–15 minutes depending on your connection speed."),
        ]:
            row = QHBoxLayout()
            row.setSpacing(12)
            lbl_i = QLabel(icon)
            lbl_i.setFixedWidth(24)
            lbl_i.setStyleSheet("font-size: 18px;")
            row.addWidget(lbl_i)
            lbl_t = QLabel(text)
            lbl_t.setWordWrap(True)
            lbl_t.setStyleSheet("color: #7a7a8a; font-size: 13px;")
            row.addWidget(lbl_t)
            layout.addLayout(row)

        layout.addStretch()


class NetworkPage(QWidget):
    """Network check + nmcli frontend if no internet."""
    net_ready    = pyqtSignal()
    net_skipped  = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(40, 20, 40, 20)
        self._layout.setSpacing(12)

        lbl = QLabel("Network Check")
        lbl.setStyleSheet("color: #e8e8f0; font-size: 18px; font-weight: 700;")
        self._layout.addWidget(lbl)

        self._status_frame = QFrame()
        self._status_frame.setStyleSheet(
            "QFrame { background: #111118; border: 1px solid #1e1e2a; border-radius: 6px; }"
        )
        sf_l = QVBoxLayout(self._status_frame)
        sf_l.setContentsMargins(16, 12, 16, 12)

        self._dot = QLabel("● Checking…")
        self._dot.setStyleSheet("color: #555; font-size: 13px; font-family: monospace;")
        sf_l.addWidget(self._dot)

        self._status_hint = QLabel("")
        self._status_hint.setStyleSheet("color: #444; font-size: 11px;")
        sf_l.addWidget(self._status_hint)
        self._layout.addWidget(self._status_frame)

        # nmcli panel (hidden by default)
        self._nmcli_frame = QFrame()
        self._nmcli_frame.setStyleSheet(
            "QFrame { background: #0d0d14; border: 1px solid #222230; border-radius: 6px; }"
        )
        nmcli_l = QVBoxLayout(self._nmcli_frame)
        nmcli_l.setContentsMargins(16, 12, 16, 12)
        nmcli_l.setSpacing(8)

        lbl_net = QLabel("Connect to a Network")
        lbl_net.setStyleSheet("color: #ddd; font-size: 14px; font-weight: 700;")
        nmcli_l.addWidget(lbl_net)

        self._wifi_list = QTextEdit()
        self._wifi_list.setReadOnly(True)
        self._wifi_list.setMaximumHeight(140)
        self._wifi_list.setPlaceholderText("Scanning for WiFi networks…")
        nmcli_l.addWidget(self._wifi_list)

        btn_row = QHBoxLayout()
        btn_scan = QPushButton("🔄 Scan WiFi")
        btn_scan.clicked.connect(self._scan_wifi)
        btn_row.addWidget(btn_scan)

        btn_eth = QPushButton("🔌 Connect Ethernet (DHCP)")
        btn_eth.clicked.connect(self._connect_eth)
        btn_row.addWidget(btn_eth)

        btn_recheck = QPushButton("✓ Re-check Internet")
        btn_recheck.setObjectName("primary")
        btn_recheck.clicked.connect(self._check_internet)
        btn_row.addWidget(btn_recheck)
        nmcli_l.addLayout(btn_row)

        from PyQt6.QtWidgets import QLineEdit
        self._ssid_input = QLineEdit()
        self._ssid_input.setPlaceholderText("WiFi SSID")
        self._ssid_input.setStyleSheet(
            "QLineEdit { background: #0a0a12; border: 1px solid #222; color: #ccc; "
            "border-radius: 4px; padding: 6px 10px; font-size: 12px; }"
        )
        self._pass_input = QLineEdit()
        self._pass_input.setPlaceholderText("Password")
        self._pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pass_input.setStyleSheet(self._ssid_input.styleSheet())
        nmcli_l.addWidget(self._ssid_input)
        nmcli_l.addWidget(self._pass_input)

        btn_connect_wifi = QPushButton("Connect to WiFi")
        btn_connect_wifi.setObjectName("primary")
        btn_connect_wifi.clicked.connect(self._connect_wifi)
        nmcli_l.addWidget(btn_connect_wifi)

        self._nmcli_output = QTextEdit()
        self._nmcli_output.setReadOnly(True)
        self._nmcli_output.setMaximumHeight(80)
        self._nmcli_output.setStyleSheet(
            "QTextEdit { background: #06060a; color: #22e87a; font-size: 11px; "
            "border: none; padding: 4px; }"
        )
        nmcli_l.addWidget(self._nmcli_output)

        self._nmcli_frame.hide()
        self._layout.addWidget(self._nmcli_frame)
        self._layout.addStretch()

        self._btn_skip = QPushButton("Skip (offline mode — container won't be pulled)")
        self._btn_skip.setObjectName("danger")
        self._btn_skip.clicked.connect(self.net_skipped.emit)
        self._layout.addWidget(self._btn_skip)

        self._check_internet()

    def _check_internet(self):
        self._dot.setText("● Checking internet…")
        self._dot.setStyleSheet("color: #eab308; font-size: 13px; font-family: monospace;")
        worker = NetCheckWorker()
        worker.result.connect(self._on_net_result)
        worker.start()
        self._worker = worker

    def _on_net_result(self, has_net: bool):
        if has_net:
            self._dot.setText("● Internet: connected")
            self._dot.setStyleSheet("color: #22c55e; font-size: 13px; font-family: monospace;")
            self._status_hint.setText("Ready to pull BlackArch container image.")
            self._nmcli_frame.hide()
            QTimer.singleShot(800, self.net_ready.emit)
        else:
            self._dot.setText("● Internet: not connected")
            self._dot.setStyleSheet("color: #ef4444; font-size: 13px; font-family: monospace;")
            self._status_hint.setText("No internet detected. Use the panel below to connect.")
            self._nmcli_frame.show()
            self._scan_wifi()

    def _scan_wifi(self):
        self._wifi_list.setPlaceholderText("Scanning…")
        try:
            out = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
                capture_output=True, text=True, timeout=8
            )
            lines = out.stdout.strip().split("\n")
            networks = []
            for line in lines:
                parts = line.split(":")
                if len(parts) >= 2 and parts[0]:
                    networks.append(f"  {parts[1]}%  {parts[0]}  [{parts[2] if len(parts) > 2 else 'open'}]")
            self._wifi_list.setText("\n".join(networks) if networks else "No WiFi networks found.")
        except FileNotFoundError:
            self._wifi_list.setText("nmcli not found. Install NetworkManager.")
        except Exception as e:
            self._wifi_list.setText(f"Error: {e}")

    def _connect_wifi(self):
        ssid = self._ssid_input.text().strip()
        pwd  = self._pass_input.text().strip()
        if not ssid:
            return
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if pwd:
            cmd += ["password", pwd]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            self._nmcli_output.setText(out.stdout + out.stderr)
            QTimer.singleShot(1500, self._check_internet)
        except Exception as e:
            self._nmcli_output.setText(f"Error: {e}")

    def _connect_eth(self):
        try:
            out = subprocess.run(
                ["nmcli", "dev", "connect", "eth0"],
                capture_output=True, text=True, timeout=10
            )
            self._nmcli_output.setText(out.stdout + out.stderr)
            QTimer.singleShot(2000, self._check_internet)
        except Exception as e:
            self._nmcli_output.setText(f"nmcli error: {e}")


class ContainerPage(QWidget):
    """Container setup progress page."""
    setup_done   = pyqtSignal(bool)

    def __init__(self, config):
        super().__init__()
        self._config = config
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(12)

        lbl = QLabel("Setting Up Container")
        lbl.setStyleSheet("color: #e8e8f0; font-size: 18px; font-weight: 700;")
        layout.addWidget(lbl)

        lbl_sub = QLabel("This will take 5–15 minutes. Please stay connected to the internet.")
        lbl_sub.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(lbl_sub)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        layout.addWidget(self._bar)

        self._step_label = QLabel("Waiting…")
        self._step_label.setStyleSheet("color: #666; font-size: 11px; font-family: monospace;")
        layout.addWidget(self._step_label)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(220)
        layout.addWidget(self._log)

        self._chk_tools = QCheckBox("Install core security tools after container creation")
        self._chk_tools.setChecked(True)
        self._chk_tools.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._chk_tools)

        self._btn_start = QPushButton("▶  Start Container Setup")
        self._btn_start.setObjectName("primary")
        self._btn_start.clicked.connect(self._start)
        layout.addWidget(self._btn_start)

        layout.addStretch()
        self._worker: ContainerSetupWorker | None = None

    def _start(self):
        self._btn_start.setEnabled(False)
        self._btn_start.setText("Setting up…")
        engine = self._config.get("container_engine", "podman")
        self._worker = ContainerSetupWorker(engine, self._chk_tools.isChecked())
        self._worker.log_line.connect(self._append)
        self._worker.progress.connect(self._bar.setValue)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _append(self, line: str):
        self._log.append(line)
        self._step_label.setText(line.strip()[:80])

    def _on_done(self, ok: bool, msg: str):
        if ok:
            self._log.append("\n✓ Container ready!")
            self._bar.setValue(100)
            self._step_label.setText("Done!")
        else:
            self._log.append(f"\n✗ Error: {msg}")
        self.setup_done.emit(ok)


class FinishPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20)
        layout.setSpacing(16)
        layout.addStretch()

        lbl = QLabel("🎉  Setup Complete!")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #22c55e; font-size: 24px; font-weight: 800;")
        layout.addWidget(lbl)

        for txt in [
            "BlackArch container is ready.",
            "Security tools are installed.",
            "Cybersecurity Mode v0.1 is ready to use.",
        ]:
            l = QLabel(f"  ✓  {txt}")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet("color: #666; font-size: 13px;")
            layout.addWidget(l)

        layout.addStretch()


# ── main wizard dialog ────────────────────────────────────────────────────────

class FirstRunWizard(QDialog):
    """
    Shown on first launch (or if container missing).
    Pages: Welcome → Network → Container → Finish
    """
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Cybersecurity Mode — First Run Setup")
        self.setModal(True)
        self.setMinimumSize(660, 520)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(48)
        hdr.setStyleSheet("QFrame { background: #080810; border-bottom: 1px solid #1a1a28; }")
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(20, 0, 20, 0)

        if ICON_PATH.exists():
            ico = QLabel()
            ico.setPixmap(
                QPixmap(str(ICON_PATH)).scaled(
                    28, 28,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            hdr_l.addWidget(ico)

        lbl_hdr = QLabel("  CYBERSECURITY MODE  —  SETUP WIZARD")
        lbl_hdr.setStyleSheet(
            "color: #444; font-size: 11px; font-weight: 700; letter-spacing: 2px; font-family: monospace;"
        )
        hdr_l.addWidget(lbl_hdr)
        hdr_l.addStretch()

        self._step_dots = QLabel("● ○ ○ ○")
        self._step_dots.setStyleSheet("color: #22c55e; font-size: 14px; letter-spacing: 4px;")
        hdr_l.addWidget(self._step_dots)
        root.addWidget(hdr)

        # ── Pages ─────────────────────────────────────────────────────────
        self._stack = QStackedWidget()

        self._page_welcome  = WelcomePage()
        self._page_network  = NetworkPage()
        self._page_container = ContainerPage(self._config)
        self._page_finish   = FinishPage()

        self._stack.addWidget(self._page_welcome)    # 0
        self._stack.addWidget(self._page_network)    # 1
        self._stack.addWidget(self._page_container)  # 2
        self._stack.addWidget(self._page_finish)     # 3
        root.addWidget(self._stack)

        # ── Footer nav ────────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(56)
        footer.setStyleSheet("QFrame { background: #080810; border-top: 1px solid #1a1a28; }")
        foot_l = QHBoxLayout(footer)
        foot_l.setContentsMargins(20, 0, 20, 0)

        self._btn_back = QPushButton("← Back")
        self._btn_back.setEnabled(False)
        self._btn_back.clicked.connect(self._go_back)
        foot_l.addWidget(self._btn_back)

        foot_l.addStretch()

        self._btn_next = QPushButton("Next →")
        self._btn_next.setObjectName("primary")
        self._btn_next.clicked.connect(self._go_next)
        foot_l.addWidget(self._btn_next)

        root.addWidget(footer)

        # ── Signals ───────────────────────────────────────────────────────
        self._page_network.net_ready.connect(lambda: self._go_to(2))
        self._page_network.net_skipped.connect(lambda: self._go_to(2))
        self._page_container.setup_done.connect(self._on_setup_done)

        self._go_to(0)

    def _go_to(self, page: int):
        self._stack.setCurrentIndex(page)
        self._btn_back.setEnabled(page > 0 and page < 3)
        dots = ["● ○ ○ ○", "○ ● ○ ○", "○ ○ ● ○", "○ ○ ○ ●"]
        self._step_dots.setText(dots[page])

        if page == 3:
            self._btn_next.setText("Launch →")
            self._btn_next.setObjectName("primary")
        elif page == 2:
            self._btn_next.hide()
        else:
            self._btn_next.show()
            self._btn_next.setText("Next →")

    def _go_next(self):
        idx = self._stack.currentIndex()
        if idx == 0:
            self._go_to(1)
        elif idx == 3:
            self.accept()

    def _go_back(self):
        idx = self._stack.currentIndex()
        if idx > 0:
            self._go_to(idx - 1)

    def _on_setup_done(self, ok: bool):
        self._config.set("container_setup_done", str(ok).lower())
        self._config.save()
        self._go_to(3)
        self._btn_next.show()
