from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTreeWidget, QTreeWidgetItem,
    QSplitter, QTextBrowser, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


# ── Documentation content ──────────────────────────────────────────────────

DOCS: dict[str, dict] = {
    "Getting Started": {
        "Welcome to Cybersecurity Mode": """
<h2 style="color:#e8e8e8">Welcome to Cybersecurity Mode</h2>
<p style="color:#aaa">Cybersecurity Mode is a professional-grade security environment built on <b>HackerOS</b>,
running tools inside an isolated <b>BlackArch Linux</b> Podman container.</p>

<h3 style="color:#e8e8e8">Two Operational Modes</h3>
<ul style="color:#aaa">
  <li><span style="color:#ef4444"><b>🔴 Red Mode</b></span> — Offensive security and penetration testing.
  Active exploitation, vulnerability research, and attack simulation.</li>
  <li><span style="color:#3b82f6"><b>🔵 Blue Mode</b></span> — Defensive security and audit.
  Monitoring, hardening, compliance analysis and incident response.</li>
</ul>

<h3 style="color:#e8e8e8">Container Architecture</h3>
<p style="color:#aaa">All security tools run inside a Podman container based on BlackArch Linux.
This ensures isolation, reproducibility, and a clean tool environment separate from your host system.</p>

<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Start the container manually
cybersec --container start

# Run a specific tool
cybersec exec nmap -sV 192.168.1.0/24

# Check container status
cybersec status
</pre>
""",
        "First Steps": """
<h2 style="color:#e8e8e8">First Steps</h2>
<p style="color:#aaa">Follow these steps to get started with Cybersecurity Mode:</p>

<h3 style="color:#22c55e">1. Start the Container</h3>
<p style="color:#aaa">Go to <b>Main</b> panel and click <b>Start Container</b>.
This will pull and start the BlackArch Linux container with all tools pre-installed.</p>

<h3 style="color:#22c55e">2. Choose Your Mode</h3>
<p style="color:#aaa">Use <b>Hacker Menu → Change Mode</b> to switch between Red and Blue mode at any time.</p>

<h3 style="color:#22c55e">3. Open the Terminal</h3>
<p style="color:#aaa">Navigate to the <b>Terminal</b> tab. The terminal connects directly to your container shell.
All commands run inside the isolated BlackArch environment.</p>

<h3 style="color:#22c55e">4. Run Your First Scan</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Basic network discovery
nmap -sn 192.168.1.0/24

# Detailed port scan
nmap -sV -sC -p- 192.168.1.100

# Save output to file
nmap -sV 192.168.1.100 -oA /results/scan1
</pre>
""",
    },
    "Penetration Testing": {
        "Reconnaissance": """
<h2 style="color:#ef4444">Reconnaissance</h2>
<p style="color:#aaa">The first phase of any pentest is gathering information about the target.</p>

<h3 style="color:#e8e8e8">Passive Reconnaissance</h3>
<p style="color:#aaa">Gather information without directly interacting with the target:</p>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# WHOIS lookup
whois target.com

# DNS enumeration
dnsenum target.com
dnsrecon -d target.com

# Certificate transparency
curl "https://crt.sh/?q=target.com&output=json" | jq .

# TheHarvester — email, subdomain discovery
theHarvester -d target.com -l 500 -b all
</pre>

<h3 style="color:#e8e8e8">Active Reconnaissance</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Host discovery
nmap -sn 192.168.1.0/24

# Port scan + service detection
nmap -sV -sC -T4 -p- 192.168.1.100

# OS fingerprinting
nmap -O 192.168.1.100

# UDP scan
nmap -sU --top-ports 200 192.168.1.100
</pre>
""",
        "Exploitation": """
<h2 style="color:#ef4444">Exploitation</h2>
<p style="color:#aaa">Using identified vulnerabilities to gain access.</p>

<h3 style="color:#e8e8e8">Metasploit Framework</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Start Metasploit console
msfconsole

# Search for exploits
msf6 > search type:exploit platform:linux

# Use an exploit
msf6 > use exploit/multi/handler
msf6 exploit(handler) > set PAYLOAD linux/x64/meterpreter/reverse_tcp
msf6 exploit(handler) > set LHOST 192.168.1.50
msf6 exploit(handler) > set LPORT 4444
msf6 exploit(handler) > run
</pre>

<h3 style="color:#e8e8e8">SQL Injection with sqlmap</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Basic injection test
sqlmap -u "http://target.com/page?id=1"

# Extract databases
sqlmap -u "http://target.com/page?id=1" --dbs

# Extract tables from specific db
sqlmap -u "http://target.com/page?id=1" -D dbname --tables

# Dump table data
sqlmap -u "http://target.com/page?id=1" -D dbname -T users --dump
</pre>
""",
        "Web Application Testing": """
<h2 style="color:#ef4444">Web Application Testing</h2>

<h3 style="color:#e8e8e8">Directory & File Discovery</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# gobuster directory scan
gobuster dir -u http://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt

# feroxbuster recursive
feroxbuster -u http://target.com -w /usr/share/seclists/Discovery/Web-Content/common.txt

# nikto web scanner
nikto -h http://target.com -o /results/nikto.html -Format htm
</pre>

<h3 style="color:#e8e8e8">Burp Suite Workflow</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
1. Configure browser proxy: 127.0.0.1:8080
2. Start Burp Suite: burpsuite
3. Intercept → On
4. Browse target application
5. Send requests to Repeater/Intruder for testing
6. Use Scanner for automated vulnerability detection
</pre>
""",
    },
    "Defensive Security": {
        "Network Monitoring": """
<h2 style="color:#3b82f6">Network Monitoring</h2>

<h3 style="color:#e8e8e8">Wireshark — Traffic Analysis</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Capture on interface
wireshark -i eth0

# Capture with filter
wireshark -i eth0 -Y "http.request.method == POST"

# tcpdump command-line
tcpdump -i eth0 -nn -w capture.pcap

# Read pcap file
tcpdump -r capture.pcap -nn port 80
</pre>

<h3 style="color:#e8e8e8">Suricata IDS</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Start Suricata on interface
suricata -c /etc/suricata/suricata.yaml -i eth0

# Test against pcap file
suricata -c /etc/suricata/suricata.yaml -r capture.pcap

# View alerts
tail -f /var/log/suricata/fast.log
</pre>
""",
        "System Hardening": """
<h2 style="color:#3b82f6">System Hardening</h2>

<h3 style="color:#e8e8e8">Lynis Security Audit</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Full system audit
lynis audit system

# Only check specific category
lynis audit system --tests-from-group authentication

# Generate report
lynis audit system --report-file /results/lynis-report.dat
</pre>

<h3 style="color:#e8e8e8">Rkhunter — Rootkit Detection</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Update database
rkhunter --update

# Run full check
rkhunter --check --skip-keypress

# Check specific directory
rkhunter --check-all --rwo
</pre>
""",
    },
    "CLI Reference": {
        "cybersec CLI": """
<h2 style="color:#e8e8e8">cybersec CLI Reference</h2>
<p style="color:#aaa">The <code style="color:#22c55e">cybersec</code> command is installed at <code style="color:#22c55e">/usr/bin/cybersec</code>.</p>

<h3 style="color:#e8e8e8">Commands</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
cybersec                   Launch Cybersecurity Mode session (TTY only)
cybersec please            Launch GUI in existing session
cybersec help              Show all available commands
cybersec update            Update tools and container image
cybersec plugin            Manage plugins (install/remove/list)
cybersec plugin install X  Install plugin X
cybersec plugin list       List installed plugins
cybersec status            Show container and system status
cybersec exec &lt;cmd&gt;       Execute command inside container
</pre>

<h3 style="color:#e8e8e8">Session Management</h3>
<pre style="background:#111;color:#22c55e;padding:12px;border-radius:6px;font-size:12px">
# Start a full Cybersecurity Mode session from TTY
cybersec

# Switch modes during session
# Use Hacker Menu → Change Mode in the GUI
# or from CLI:
cybersec set-mode red
cybersec set-mode blue
</pre>
""",
    },
}


class DocsPanel(QWidget):
    def __init__(self, config):
        super().__init__()
        self._config = config
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: tree navigator
        left = QWidget()
        left.setFixedWidth(240)
        left.setStyleSheet("background: #181818; border-right: 1px solid #2e2e2e;")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(0)

        search = QLineEdit()
        search.setPlaceholderText("Search docs…")
        search.setStyleSheet(
            "background: #111; color: #e8e8e8; border: none; "
            "border-bottom: 1px solid #2e2e2e; padding: 8px 12px; font-size: 12px;"
        )
        left_l.addWidget(search)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background: #181818;
                color: #aaa;
                border: none;
                font-size: 12px;
            }
            QTreeWidget::item { padding: 5px 8px; }
            QTreeWidget::item:selected {
                background: #2a2a2a;
                color: #e8e8e8;
            }
            QTreeWidget::item:hover { background: #222; }
            QTreeWidget::branch { background: #181818; }
        """)
        self._populate_tree()
        self._tree.itemClicked.connect(self._on_item_click)
        left_l.addWidget(self._tree)

        splitter.addWidget(left)

        # Right: content browser
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet("""
            QTextBrowser {
                background: #1a1a1a;
                color: #ccc;
                border: none;
                padding: 24px 32px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        right_l.addWidget(self._browser)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Show welcome page
        self._show_content("Getting Started", "Welcome to Cybersecurity Mode")

    def _populate_tree(self):
        for section, pages in DOCS.items():
            parent = QTreeWidgetItem(self._tree, [section])
            parent.setExpanded(True)
            for page in pages:
                child = QTreeWidgetItem(parent, [page])
                child.setData(0, Qt.ItemDataRole.UserRole, (section, page))

    def _on_item_click(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            section, page = data
            self._show_content(section, page)

    def _show_content(self, section: str, page: str):
        html = DOCS.get(section, {}).get(page, "<p>Page not found.</p>")
        self._browser.setHtml(f"""
        <html><body style="font-family: 'JetBrains Mono', monospace;
                           background:#1a1a1a; color:#ccc; padding:0; margin:0;">
        {html}
        </body></html>
        """)
