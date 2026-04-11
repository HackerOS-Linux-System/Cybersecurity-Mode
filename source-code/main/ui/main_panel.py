"""
ui/main_panel.py — Main dashboard panel (tools, container status, quick actions)
"""
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
# Each entry: (command, description, icon, color, category)

RED_TOOLS = [
    # ── Reconnaissance ──────────────────────────────────────────────────────
    ("nmap",            "Network discovery & port scan",       "🔍", "#ef4444", "Recon"),
    ("masscan",         "Mass port scanner (async)",           "⚡", "#ef4444", "Recon"),
    ("rustscan",        "Fast port scanner, Rust-based",       "🦀", "#f97316", "Recon"),
    ("theHarvester",    "Email / subdomain / OSINT harvester", "🌾", "#eab308", "Recon"),
    ("maltego",         "Visual link analysis / OSINT",        "🕸",  "#f97316", "Recon"),
    ("shodan",          "Internet-connected device search",    "👁",  "#eab308", "Recon"),
    ("recon-ng",        "Web reconnaissance framework",        "🔭", "#ef4444", "Recon"),
    ("dnsenum",         "DNS enumeration & brute-force",       "🌐", "#f97316", "Recon"),
    ("dnsrecon",        "DNS enumeration & zone transfer",     "📡", "#eab308", "Recon"),
    ("amass",           "In-depth attack surface mapping",     "🗺",  "#ef4444", "Recon"),
    ("subfinder",       "Subdomain discovery",                 "🔎", "#f97316", "Recon"),
    ("whois",           "Domain registration lookup",          "📋", "#eab308", "Recon"),
    ("fierce",          "DNS recon & host discovery",          "🦁", "#ef4444", "Recon"),
    ("enum4linux",      "SMB/NetBIOS enumeration",             "🪟", "#f97316", "Recon"),
    ("netdiscover",     "ARP network discovery",               "📻", "#eab308", "Recon"),

    # ── Web Application ──────────────────────────────────────────────────────
    ("burpsuite",       "Web proxy, scanner & attack suite",   "🕷",  "#ef4444", "Web"),
    ("sqlmap",          "SQL injection automation",            "🗄",  "#ef4444", "Web"),
    ("nikto",           "Web server vulnerability scanner",    "🌐", "#f97316", "Web"),
    ("gobuster",        "Dir/DNS/vhost brute-force",           "📂", "#ef4444", "Web"),
    ("feroxbuster",     "Recursive content discovery",         "🐾", "#f97316", "Web"),
    ("ffuf",            "Fast web fuzzer",                     "⚡", "#eab308", "Web"),
    ("wfuzz",           "Web application fuzzer",              "🌀", "#ef4444", "Web"),
    ("dirsearch",       "Web path brute-force scanner",        "🗂",  "#f97316", "Web"),
    ("whatweb",         "Web fingerprinting",                  "🔬", "#eab308", "Web"),
    ("nuclei",          "Template-based vulnerability scanner","☢",  "#ef4444", "Web"),
    ("dalfox",          "XSS scanner & parameter analysis",    "🦊", "#f97316", "Web"),
    ("xsstrike",        "Advanced XSS detection suite",        "⚔",  "#eab308", "Web"),
    ("commix",          "Command injection exploiter",         "💥", "#ef4444", "Web"),
    ("joomscan",        "Joomla vulnerability scanner",        "🌴", "#f97316", "Web"),
    ("wpscan",          "WordPress security scanner",          "📰", "#eab308", "Web"),

    # ── Exploitation ──────────────────────────────────────────────────────────
    ("msfconsole",      "Metasploit exploitation framework",   "💉", "#ef4444", "Exploit"),
    ("searchsploit",    "ExploitDB offline search",            "📚", "#ef4444", "Exploit"),
    ("exploit-db",      "Public exploit database browser",     "💣", "#f97316", "Exploit"),
    ("beef-xss",        "Browser exploitation framework",      "🐄", "#eab308", "Exploit"),
    ("setoolkit",       "Social engineering toolkit",          "🎭", "#ef4444", "Exploit"),
    ("impacket",        "Network protocol attack toolkit",     "📦", "#f97316", "Exploit"),
    ("responder",       "LLMNR/NBT-NS/mDNS poisoner",         "☠",  "#ef4444", "Exploit"),
    ("certipy",         "Active Directory cert abuse",         "📜", "#f97316", "Exploit"),
    ("evil-winrm",      "WinRM shell for pentesting",          "👿", "#eab308", "Exploit"),
    ("crackmapexec",    "SMB/WinRM/LDAP network scanner",      "🗺",  "#ef4444", "Exploit"),

    # ── Password Attacks ──────────────────────────────────────────────────────
    ("hashcat",         "GPU-accelerated password cracking",   "🔓", "#ef4444", "Passwords"),
    ("john",            "John the Ripper password cracker",    "🔐", "#f97316", "Passwords"),
    ("hydra",           "Network login brute-forcer",          "🔑", "#ef4444", "Passwords"),
    ("medusa",          "Parallel network login auditor",      "🐍", "#f97316", "Passwords"),
    ("cewl",            "Custom wordlist generator",           "📝", "#eab308", "Passwords"),
    ("crunch",          "Wordlist generator",                  "⚙",  "#ef4444", "Passwords"),
    ("cupp",            "Common user passwords profiler",      "👤", "#f97316", "Passwords"),
    ("ophcrack",        "Windows password cracker (rainbow)",  "🌈", "#eab308", "Passwords"),

    # ── Network ───────────────────────────────────────────────────────────────
    ("netcat",          "TCP/IP swiss army knife",             "🔌", "#22c55e", "Network"),
    ("ncat",            "Nmap project netcat replacement",     "🔗", "#22c55e", "Network"),
    ("tcpdump",         "CLI packet capture & analysis",       "📡", "#3b82f6", "Network"),
    ("wireshark",       "GUI packet analyzer",                 "📶", "#3b82f6", "Network"),
    ("tshark",          "Terminal Wireshark",                  "🦈", "#3b82f6", "Network"),
    ("scapy",           "Interactive packet manipulation",     "🐍", "#22c55e", "Network"),
    ("hping3",          "TCP/IP packet generator",             "🏓", "#ef4444", "Network"),
    ("netsniff-ng",     "Linux network analyzer toolkit",      "🎣", "#3b82f6", "Network"),
    ("bettercap",       "Network attacks & MitM framework",    "🎯", "#ef4444", "Network"),
    ("ettercap",        "Man-in-the-Middle attack suite",      "🕵",  "#ef4444", "Network"),
    ("arpspoof",        "ARP cache poisoning tool",            "☠",  "#ef4444", "Network"),
    ("sslstrip",        "HTTPS stripping attack",              "🔓", "#ef4444", "Network"),
    ("proxychains",     "Route traffic through proxies",       "⛓",  "#eab308", "Network"),
    ("tor",             "Anonymity network client",            "🧅", "#eab308", "Network"),
    ("stunnel",         "SSL/TLS tunneling",                   "🚇", "#22c55e", "Network"),

    # ── Wireless ──────────────────────────────────────────────────────────────
    ("aircrack-ng",     "WiFi WEP/WPA/WPA2 cracking suite",   "📡", "#eab308", "Wireless"),
    ("airmon-ng",       "Wireless monitor mode manager",       "📻", "#eab308", "Wireless"),
    ("airodump-ng",     "WiFi packet capture",                 "📸", "#ef4444", "Wireless"),
    ("aireplay-ng",     "WiFi packet injection",               "💥", "#ef4444", "Wireless"),
    ("wifite",          "Automated wireless auditor",          "🤖", "#eab308", "Wireless"),
    ("hostapd-wpe",     "Rogue AP for credential harvest",     "📶", "#ef4444", "Wireless"),
    ("bully",           "WPS brute-force attack",              "🐂", "#f97316", "Wireless"),

    # ── Forensics / Reverse ────────────────────────────────────────────────────
    ("binwalk",         "Firmware analysis & extraction",      "🔍", "#f97316", "Forensics"),
    ("volatility3",     "Memory forensics framework",          "🧠", "#ef4444", "Forensics"),
    ("autopsy",         "Digital forensics platform",          "🔬", "#f97316", "Forensics"),
    ("ghidra",          "NSA reverse engineering suite",       "🐉", "#ef4444", "Forensics"),
    ("radare2",         "Reverse engineering framework",       "🔭", "#f97316", "Forensics"),
    ("gdb",             "GNU debugger with PEDA/pwndbg",       "🐛", "#eab308", "Forensics"),
    ("strace",          "System call tracer",                  "📊", "#22c55e", "Forensics"),
    ("strings",         "Extract printable strings",           "📜", "#eab308", "Forensics"),
    ("file",            "Determine file type",                 "📁", "#22c55e", "Forensics"),
    ("exiftool",        "Metadata extraction",                 "📷", "#f97316", "Forensics"),
    ("foremost",        "File carving / recovery",             "⛏",  "#ef4444", "Forensics"),
    ("pwntools",        "CTF exploit development library",     "🏴", "#ef4444", "Forensics"),
    ("checksec",        "Binary security property checker",    "🛡",  "#22c55e", "Forensics"),

    # ── Post-Exploitation ──────────────────────────────────────────────────────
    ("mimikatz",        "Windows credential dumper",           "🔑", "#ef4444", "Post-Exploit"),
    ("bloodhound",      "AD attack path visualizer",           "🐕", "#ef4444", "Post-Exploit"),
    ("neo4j",           "BloodHound graph database",           "🗄",  "#f97316", "Post-Exploit"),
    ("powercat",        "PowerShell netcat",                   "⚡", "#ef4444", "Post-Exploit"),
    ("chisel",          "TCP/UDP tunnel over HTTP",            "🪓", "#f97316", "Post-Exploit"),
    ("ligolo-ng",       "Tunneling / pivoting agent",          "🌀", "#ef4444", "Post-Exploit"),
    ("pspy",            "Unprivileged process monitor",        "👁",  "#eab308", "Post-Exploit"),
    ("linpeas",         "Linux privilege escalation scanner",  "🐧", "#ef4444", "Post-Exploit"),
    ("winpeas",         "Windows privilege escalation scanner","🪟", "#ef4444", "Post-Exploit"),
    ("gtfobins",        "Unix binary abuse reference",         "📚", "#f97316", "Post-Exploit"),
    ("lolbas",          "Living off the Land Binaries (Win)",  "🪟", "#f97316", "Post-Exploit"),
]

BLUE_TOOLS = [
    # ── Network Monitoring ────────────────────────────────────────────────────
    ("wireshark",       "GUI packet analyzer",                 "📶", "#3b82f6", "Monitoring"),
    ("tshark",          "CLI packet capture & analysis",       "🦈", "#3b82f6", "Monitoring"),
    ("tcpdump",         "Lightweight packet capture",          "📡", "#22c55e", "Monitoring"),
    ("zeek",            "Network security monitor",            "🦓", "#3b82f6", "Monitoring"),
    ("arkime",          "Full PCAP capture & search",          "🌊", "#3b82f6", "Monitoring"),
    ("ntopng",          "Network traffic flow monitor",        "📊", "#22c55e", "Monitoring"),
    ("netflow",         "Traffic flow analysis",               "🌊", "#3b82f6", "Monitoring"),
    ("iftop",           "Bandwidth usage by connection",       "📈", "#22c55e", "Monitoring"),
    ("iptraf-ng",       "Interactive IP traffic monitor",      "🖥",  "#3b82f6", "Monitoring"),
    ("nethogs",         "Per-process bandwidth monitor",       "🐷", "#22c55e", "Monitoring"),
    ("ss",              "Socket statistics",                   "🔌", "#22c55e", "Monitoring"),
    ("netstat",         "Network connections & routing",       "🗺",  "#3b82f6", "Monitoring"),

    # ── IDS / IPS ─────────────────────────────────────────────────────────────
    ("suricata",        "High-performance IDS/IPS/NSM",        "🛡",  "#3b82f6", "IDS/IPS"),
    ("snort",           "Network intrusion detection",         "👃", "#3b82f6", "IDS/IPS"),
    ("ossec",           "Host-based IDS (HIDS)",               "🏠", "#22c55e", "IDS/IPS"),
    ("wazuh",           "SIEM + XDR platform",                 "🔐", "#3b82f6", "IDS/IPS"),
    ("aide",            "File integrity checker",              "📋", "#22c55e", "IDS/IPS"),
    ("samhain",         "File integrity + HIDS",               "🔮", "#3b82f6", "IDS/IPS"),
    ("fail2ban",        "Log-based intrusion prevention",      "🚫", "#22c55e", "IDS/IPS"),
    ("psad",            "Port scan attack detector",           "🎯", "#3b82f6", "IDS/IPS"),
    ("tripwire",        "File integrity monitoring",           "🕸",  "#22c55e", "IDS/IPS"),

    # ── Vulnerability Scanning ─────────────────────────────────────────────────
    ("openvas",         "Full-featured vulnerability scanner", "🩺", "#3b82f6", "Scanning"),
    ("nessus",          "Commercial vuln scanner (free home)", "🔬", "#3b82f6", "Scanning"),
    ("nmap",            "Port scan + NSE scripts",             "🔍", "#22c55e", "Scanning"),
    ("nuclei",          "Template-based vuln scanner",         "☢",  "#3b82f6", "Scanning"),
    ("lynis",           "Security auditing & hardening",       "🔎", "#22c55e", "Scanning"),
    ("vulmap",          "Online local exploit suggester",      "🗺",  "#3b82f6", "Scanning"),
    ("cve-search",      "CVE lookup & analysis",               "📚", "#22c55e", "Scanning"),
    ("grype",           "Container image vulnerability scan",  "📦", "#3b82f6", "Scanning"),
    ("trivy",           "Container & filesystem vuln scan",    "🔭", "#22c55e", "Scanning"),
    ("prowler",         "AWS/GCP/Azure security assessment",   "☁",  "#3b82f6", "Scanning"),

    # ── System Hardening ──────────────────────────────────────────────────────
    ("auditd",          "Linux kernel audit daemon",           "📋", "#22c55e", "Hardening"),
    ("apparmor",        "Mandatory access control",            "🔒", "#22c55e", "Hardening"),
    ("selinux",         "SELinux policy manager",              "🛡",  "#3b82f6", "Hardening"),
    ("ufw",             "Uncomplicated firewall manager",      "🔥", "#22c55e", "Hardening"),
    ("iptables",        "Netfilter firewall rules",            "⛓",  "#3b82f6", "Hardening"),
    ("nftables",        "Modern Linux firewall",               "🔥", "#22c55e", "Hardening"),
    ("chkrootkit",      "Rootkit detection scanner",           "🔦", "#22c55e", "Hardening"),
    ("rkhunter",        "Rootkit + backdoor hunter",           "🕵",  "#22c55e", "Hardening"),
    ("debsums",         "Verify package integrity (Debian)",   "✅", "#22c55e", "Hardening"),
    ("tiger",           "UNIX security audit",                 "🐯", "#3b82f6", "Hardening"),
    ("bastille",        "System hardening automation",         "🏰", "#22c55e", "Hardening"),
    ("pass",            "Password store (GPG-encrypted)",      "🔑", "#22c55e", "Hardening"),
    ("age",             "Modern file encryption tool",         "🔒", "#3b82f6", "Hardening"),

    # ── Malware Analysis ──────────────────────────────────────────────────────
    ("clamav",          "Open-source antivirus engine",        "🦠",  "#3b82f6", "Malware"),
    ("yara",            "Malware pattern matching",            "🎯", "#ef4444", "Malware"),
    ("volatility3",     "Memory forensics & malware analysis", "🧠", "#ef4444", "Malware"),
    ("ghidra",          "Malware reverse engineering",         "🐉", "#ef4444", "Malware"),
    ("radare2",         "Binary analysis framework",           "🔭", "#f97316", "Malware"),
    ("cuckoo",          "Automated malware sandbox",           "🐦", "#ef4444", "Malware"),
    ("binwalk",         "Firmware extraction & analysis",      "🔍", "#f97316", "Malware"),
    ("strings",         "Extract printable strings",           "📜", "#22c55e", "Malware"),
    ("exiftool",        "File metadata extraction",            "📷", "#22c55e", "Malware"),

    # ── Log Analysis / SIEM ────────────────────────────────────────────────────
    ("elk",             "Elasticsearch / Logstash / Kibana",   "🔎", "#3b82f6", "SIEM"),
    ("graylog",         "Log management platform",             "📊", "#3b82f6", "SIEM"),
    ("loki",            "Grafana log aggregation",             "🗂",  "#22c55e", "SIEM"),
    ("grafana",         "Metrics & log visualization",         "📈", "#f97316", "SIEM"),
    ("splunk",          "Security data analytics platform",    "🔮", "#3b82f6", "SIEM"),
    ("chainsaw",        "Windows event log analysis",          "⛓",  "#22c55e", "SIEM"),
    ("sigma",           "Generic SIEM rule format",            "Σ",  "#3b82f6", "SIEM"),
    ("timesketch",      "Collaborative timeline analysis",     "⏱",  "#22c55e", "SIEM"),

    # ── Digital Forensics ─────────────────────────────────────────────────────
    ("autopsy",         "Digital forensics platform",          "🔬", "#f97316", "Forensics"),
    ("sleuthkit",       "Filesystem analysis tools",           "🔍", "#22c55e", "Forensics"),
    ("foremost",        "File carving & data recovery",        "⛏",  "#f97316", "Forensics"),
    ("photorec",        "File recovery from disk",             "📸", "#22c55e", "Forensics"),
    ("dd",              "Raw disk image creation",             "💿", "#22c55e", "Forensics"),
    ("dc3dd",           "Forensic disk copy with hashing",     "🔐", "#22c55e", "Forensics"),
    ("testdisk",        "Partition recovery tool",             "💾", "#3b82f6", "Forensics"),

    # ── Compliance / Audit ─────────────────────────────────────────────────────
    ("openscap",        "SCAP compliance scanner",             "📋", "#3b82f6", "Compliance"),
    ("inspec",          "Compliance-as-code framework",        "✅", "#22c55e", "Compliance"),
    ("ansible-hardening","Automated system hardening",         "🤖", "#22c55e", "Compliance"),
    ("scoutsuite",      "Multi-cloud security audit",          "☁",  "#3b82f6", "Compliance"),
    ("prowler",         "CIS benchmark compliance check",      "🎖",  "#22c55e", "Compliance"),
    ("dockle",          "Container image security linter",     "🐳", "#3b82f6", "Compliance"),
    ("kube-bench",      "CIS Kubernetes benchmark",            "☸",  "#3b82f6", "Compliance"),
]


class ToolCard(QFrame):
    def __init__(self, name: str, desc: str, icon: str, color: str,
                 category: str, ipc):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(96)
        self._name = name
        self._category = category
        self._ipc  = ipc

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        row = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 18px;")
        row.addWidget(lbl_icon)

        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 700; "
            "font-family: 'JetBrains Mono', monospace;"
        )
        row.addWidget(lbl_name)
        row.addStretch()

        # Category badge
        lbl_cat = QLabel(category)
        lbl_cat.setStyleSheet(
            f"color: {color}99; font-size: 9px; font-weight: 700; "
            f"background: {color}15; border: 1px solid {color}30; "
            "border-radius: 3px; padding: 1px 5px; letter-spacing: 0.5px;"
        )
        row.addWidget(lbl_cat)

        btn_run = QPushButton("▶")
        btn_run.setFixedSize(28, 24)
        btn_run.setStyleSheet(
            f"background: {color}22; border: 1px solid {color}55; "
            f"color: {color}; border-radius: 4px; font-size: 12px; margin-left: 6px;"
        )
        btn_run.clicked.connect(self._launch)
        btn_run.setToolTip(f"Open {name} in terminal")
        row.addWidget(btn_run)
        layout.addLayout(row)

        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("color: #606070; font-size: 11px;")
        lbl_desc.setWordWrap(True)
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
        self._active_cat = "All"
        self._build()

    def _get_categories(self) -> list[str]:
        mode  = self._config.get("mode", "red")
        tools = RED_TOOLS if mode == "red" else BLUE_TOOLS
        cats  = ["All"] + list(dict.fromkeys(t[4] for t in tools))
        return cats

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── Header row ────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        self._lbl_title = QLabel()
        self._lbl_title.setObjectName("panelTitle")
        self._update_title()
        hdr.addWidget(self._lbl_title)
        hdr.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search tools…")
        self._search.setFixedWidth(200)
        self._search.setFixedHeight(30)
        self._search.textChanged.connect(self._filter_tools)
        hdr.addWidget(self._search)
        layout.addLayout(hdr)

        # ── Container status ───────────────────────────────────────────────
        self._container_status = ContainerStatusWidget(self._ipc)
        layout.addWidget(self._container_status)

        # ── Category filter bar ────────────────────────────────────────────
        self._cat_bar_widget = QWidget()
        self._cat_bar_layout = QHBoxLayout(self._cat_bar_widget)
        self._cat_bar_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_bar_layout.setSpacing(6)
        self._cat_buttons: dict[str, QPushButton] = {}
        layout.addWidget(self._cat_bar_widget)

        # ── Tool count label ───────────────────────────────────────────────
        self._lbl_count = QLabel()
        self._lbl_count.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(self._lbl_count)

        # ── Tools grid (scrollable) ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._tools_container = QWidget()
        self._tools_grid = QGridLayout(self._tools_container)
        self._tools_grid.setSpacing(10)
        self._tools_grid.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._tools_container)
        layout.addWidget(scroll)

        self._tool_cards: list[ToolCard] = []
        self._populate_all()

    def _build_cat_bar(self):
        # Clear old buttons
        for btn in self._cat_buttons.values():
            btn.deleteLater()
        self._cat_buttons.clear()

        mode  = self._config.get("mode", "red")
        accent = "#ef4444" if mode == "red" else "#3b82f6"

        for cat in self._get_categories():
            btn = QPushButton(cat)
            btn.setFixedHeight(26)
            btn.setCheckable(False)
            is_active = cat == self._active_cat
            btn.setStyleSheet(
                f"QPushButton {{ background: {'%s22' % accent if is_active else '#1e1e1e'}; "
                f"border: 1px solid {'%s66' % accent if is_active else '#2e2e2e'}; "
                f"color: {'%s' % accent if is_active else '#777'}; "
                f"border-radius: 4px; padding: 0 10px; font-size: 11px; font-weight: {'700' if is_active else '400'}; }}"
                f"QPushButton:hover {{ background: #2a2a2a; color: #ccc; }}"
            )
            btn.clicked.connect(lambda _, c=cat: self._set_category(c))
            self._cat_bar_layout.addWidget(btn)
            self._cat_buttons[cat] = btn

        self._cat_bar_layout.addStretch()

    def _set_category(self, cat: str):
        self._active_cat = cat
        self._build_cat_bar()
        self._filter_tools(self._search.text())

    def _update_title(self):
        mode = self._config.get("mode", "red")
        if mode == "red":
            self._lbl_title.setText("⚔  Offensive / Pentest")
            self._lbl_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #ef4444;")
        else:
            self._lbl_title.setText("🛡  Defensive / Audit")
            self._lbl_title.setStyleSheet("font-size: 17px; font-weight: 700; color: #3b82f6;")

    def _populate_all(self):
        for c in self._tool_cards:
            c.deleteLater()
        self._tool_cards.clear()

        mode  = self._config.get("mode", "red")
        tools = RED_TOOLS if mode == "red" else BLUE_TOOLS
        COLS  = 3

        for i, (name, desc, icon, color, category) in enumerate(tools):
            card = ToolCard(name, desc, icon, color, category, self._ipc)
            self._tools_grid.addWidget(card, i // COLS, i % COLS)
            self._tool_cards.append(card)

        self._active_cat = "All"
        self._build_cat_bar()
        self._update_count()

    def _filter_tools(self, text: str):
        text = text.lower().strip()
        visible = 0
        col_idx = 0
        row_idx = 0
        COLS = 3

        for card in self._tool_cards:
            cat_ok  = (self._active_cat == "All" or card._category == self._active_cat)
            text_ok = (not text or text in card._name.lower())
            show    = cat_ok and text_ok
            card.setVisible(show)
            if show:
                # Re-position in grid so there are no gaps
                self._tools_grid.removeWidget(card)
                self._tools_grid.addWidget(card, row_idx, col_idx)
                col_idx += 1
                if col_idx >= COLS:
                    col_idx = 0
                    row_idx += 1
                visible += 1

        self._update_count(visible)

    def _update_count(self, visible: int = None):
        mode  = self._config.get("mode", "red")
        total = len(RED_TOOLS if mode == "red" else BLUE_TOOLS)
        shown = visible if visible is not None else total
        self._lbl_count.setText(f"Showing {shown} of {total} tools")

    @pyqtSlot(str)
    def on_mode_changed(self, mode: str):
        self._update_title()
        self._populate_all()
