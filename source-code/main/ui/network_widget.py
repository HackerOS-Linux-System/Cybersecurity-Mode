from __future__ import annotations

import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTextEdit, QComboBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal


# ── worker ────────────────────────────────────────────────────────────────────

class NMWorker(QThread):
    result = pyqtSignal(str)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self._cmd = cmd

    def run(self):
        try:
            out = subprocess.run(
                self._cmd, capture_output=True, text=True, timeout=15
            )
            self.result.emit((out.stdout + out.stderr).strip())
        except FileNotFoundError:
            self.result.emit("nmcli not found. Install NetworkManager.")
        except subprocess.TimeoutExpired:
            self.result.emit("Timeout.")
        except Exception as e:
            self.result.emit(f"Error: {e}")


# ── main widget ───────────────────────────────────────────────────────────────

class NetworkManagerWidget(QWidget):
    """
    nmcli frontend.
    Embedded in Settings panel under a "Network" section.
    """
    STYLE = """
    QFrame#nmcard {
        background: #111118; border: 1px solid #1e1e2a; border-radius: 6px;
    }
    QLabel { color: #aaa; font-size: 12px; }
    QLineEdit {
        background: #0a0a12; border: 1px solid #222; color: #ccc;
        border-radius: 4px; padding: 5px 8px; font-size: 12px;
    }
    QPushButton {
        background: #16161e; border: 1px solid #2a2a38; color: #aaa;
        border-radius: 4px; padding: 5px 12px; font-size: 11px;
    }
    QPushButton:hover { background: #1e1e2a; color: #ddd; }
    QPushButton#green {
        background: #0a180a; border-color: #22c55e44; color: #22c55e; font-weight: 700;
    }
    QPushButton#green:hover { background: #22c55e22; }
    QPushButton#red {
        background: #180a0a; border-color: #ef444444; color: #ef4444; font-weight: 700;
    }
    QTextEdit {
        background: #07070d; color: #22e87a; border: 1px solid #1a1a24;
        border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 11px;
        padding: 4px;
    }
    QComboBox {
        background: #0a0a12; border: 1px solid #222; color: #ccc;
        border-radius: 4px; padding: 4px 8px; font-size: 12px;
    }
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.STYLE)
        self._workers: list[NMWorker] = []
        self._build()
        QTimer.singleShot(300, self._refresh_status)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── Status card ───────────────────────────────────────────────────
        status_card = QFrame()
        status_card.setObjectName("nmcard")
        sc_l = QVBoxLayout(status_card)
        sc_l.setContentsMargins(14, 12, 14, 12)
        sc_l.setSpacing(6)

        hdr = QHBoxLayout()
        lbl_title = QLabel("Network Status")
        lbl_title.setStyleSheet(
            "color: #ddd; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;"
        )
        hdr.addWidget(lbl_title)
        hdr.addStretch()
        btn_refresh = QPushButton("⟳ Refresh")
        btn_refresh.setFixedHeight(24)
        btn_refresh.clicked.connect(self._refresh_status)
        hdr.addWidget(btn_refresh)
        sc_l.addLayout(hdr)

        self._status_text = QTextEdit()
        self._status_text.setReadOnly(True)
        self._status_text.setMaximumHeight(100)
        sc_l.addWidget(self._status_text)
        root.addWidget(status_card)

        # ── WiFi card ─────────────────────────────────────────────────────
        wifi_card = QFrame()
        wifi_card.setObjectName("nmcard")
        wc_l = QVBoxLayout(wifi_card)
        wc_l.setContentsMargins(14, 12, 14, 12)
        wc_l.setSpacing(8)

        wc_hdr = QHBoxLayout()
        lbl_wifi = QLabel("WiFi")
        lbl_wifi.setStyleSheet("color: #ddd; font-size: 13px; font-weight: 700;")
        wc_hdr.addWidget(lbl_wifi)
        wc_hdr.addStretch()
        btn_scan = QPushButton("Scan")
        btn_scan.setFixedHeight(24)
        btn_scan.clicked.connect(self._scan_wifi)
        wc_hdr.addWidget(btn_scan)
        wc_l.addLayout(wc_hdr)

        self._wifi_combo = QComboBox()
        self._wifi_combo.setPlaceholderText("Select network…")
        wc_l.addWidget(self._wifi_combo)

        pw_row = QHBoxLayout()
        self._pw_input = QLineEdit()
        self._pw_input.setPlaceholderText("Password (leave empty for open network)")
        self._pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        pw_row.addWidget(self._pw_input)

        self._btn_show_pw = QPushButton("👁")
        self._btn_show_pw.setFixedSize(30, 28)
        self._btn_show_pw.setCheckable(True)
        self._btn_show_pw.toggled.connect(
            lambda on: self._pw_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        pw_row.addWidget(self._btn_show_pw)
        wc_l.addLayout(pw_row)

        btn_row = QHBoxLayout()
        btn_connect = QPushButton("Connect WiFi")
        btn_connect.setObjectName("green")
        btn_connect.clicked.connect(self._connect_wifi)
        btn_row.addWidget(btn_connect)

        btn_disconnect = QPushButton("Disconnect")
        btn_disconnect.setObjectName("red")
        btn_disconnect.clicked.connect(self._disconnect)
        btn_row.addWidget(btn_disconnect)
        wc_l.addLayout(btn_row)
        root.addWidget(wifi_card)

        # ── Ethernet card ─────────────────────────────────────────────────
        eth_card = QFrame()
        eth_card.setObjectName("nmcard")
        ec_l = QVBoxLayout(eth_card)
        ec_l.setContentsMargins(14, 12, 14, 12)
        ec_l.setSpacing(8)

        lbl_eth = QLabel("Ethernet")
        lbl_eth.setStyleSheet("color: #ddd; font-size: 13px; font-weight: 700;")
        ec_l.addWidget(lbl_eth)

        eth_btns = QHBoxLayout()
        for label, fn in [
            ("Connect (DHCP)",  self._eth_dhcp),
            ("Set Static IP…",  self._eth_static_dialog),
            ("Disconnect",      self._eth_disconnect),
        ]:
            b = QPushButton(label)
            b.setFixedHeight(28)
            b.clicked.connect(fn)
            eth_btns.addWidget(b)
        ec_l.addLayout(eth_btns)
        root.addWidget(eth_card)

        # ── Output log ────────────────────────────────────────────────────
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(80)
        self._log.setPlaceholderText("nmcli output…")
        root.addWidget(self._log)

    # ── nmcli calls ───────────────────────────────────────────────────────

    def _run(self, cmd: list[str], callback=None):
        w = NMWorker(cmd)
        if callback:
            w.result.connect(callback)
        else:
            w.result.connect(self._log.append)
        w.start()
        self._workers.append(w)

    def _refresh_status(self):
        self._run(
            ["nmcli", "-p", "dev", "status"],
            lambda s: self._status_text.setText(s)
        )

    def _scan_wifi(self):
        self._wifi_combo.clear()
        self._wifi_combo.addItem("Scanning…")

        def on_result(raw: str):
            self._wifi_combo.clear()
            for line in raw.strip().splitlines():
                parts = line.split(":")
                ssid = parts[0].strip() if parts else ""
                if ssid and ssid != "--":
                    signal = parts[1].strip() if len(parts) > 1 else "?"
                    sec    = parts[2].strip() if len(parts) > 2 else "open"
                    self._wifi_combo.addItem(f"{ssid}  ({signal}%  {sec})", userData=ssid)

        self._run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
            on_result
        )

    def _connect_wifi(self):
        ssid = self._wifi_combo.currentData() or self._wifi_combo.currentText().split("(")[0].strip()
        pwd  = self._pw_input.text().strip()
        if not ssid:
            return
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if pwd:
            cmd += ["password", pwd]
        self._run(cmd)
        QTimer.singleShot(2000, self._refresh_status)

    def _disconnect(self):
        self._run(["nmcli", "dev", "disconnect", "wlan0"])
        QTimer.singleShot(1000, self._refresh_status)

    def _eth_dhcp(self):
        self._run(["nmcli", "dev", "connect", "eth0"])
        QTimer.singleShot(2000, self._refresh_status)

    def _eth_disconnect(self):
        self._run(["nmcli", "dev", "disconnect", "eth0"])
        QTimer.singleShot(1000, self._refresh_status)

    def _eth_static_dialog(self):
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Static IP Configuration")
        dlg.setStyleSheet(
            "QDialog { background: #0d0d14; }"
            "QLabel { color: #aaa; } "
            "QLineEdit { background: #0a0a12; border: 1px solid #222; "
            "color: #ccc; border-radius: 4px; padding: 5px 8px; }"
        )
        fl = QFormLayout(dlg)
        ip_e   = QLineEdit("192.168.1.100/24")
        gw_e   = QLineEdit("192.168.1.1")
        dns_e  = QLineEdit("8.8.8.8,1.1.1.1")
        fl.addRow("IP/prefix:",  ip_e)
        fl.addRow("Gateway:",    gw_e)
        fl.addRow("DNS:",        dns_e)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        fl.addRow(bb)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._run([
                "nmcli", "con", "modify", "Wired connection 1",
                "ipv4.method", "manual",
                "ipv4.addresses", ip_e.text(),
                "ipv4.gateway",   gw_e.text(),
                "ipv4.dns",       dns_e.text(),
            ])
            self._run(["nmcli", "con", "up", "Wired connection 1"])
            QTimer.singleShot(2000, self._refresh_status)
