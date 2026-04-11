from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QLineEdit, QSizePolicy,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

# ── Tool catalog ────────────────────────────────────────────────────────────
# (command, description, icon, color, category)

RED_TOOLS: list[tuple[str, str, str, str, str]] = [
    # ── Reconnaissance ─────────────────────────────────────────────────────
    ("nmap",            "Network discovery & port scanner",        "🔍", "#ef4444", "Recon"),
    ("masscan",         "Mass port scanner — fastest",             "⚡", "#ef4444", "Recon"),
    ("rustscan",        "Rust-based ultra-fast port scanner",      "🦀", "#f97316", "Recon"),
    ("theHarvester",    "OSINT: emails, subdomains, IPs",          "🌾", "#eab308", "Recon"),
    ("amass",           "In-depth attack surface mapping",         "🗺",  "#ef4444", "Recon"),
    ("subfinder",       "Passive subdomain discovery",             "🔎", "#f97316", "Recon"),
    ("recon-ng",        "Web reconnaissance framework",            "🔭", "#eab308", "Recon"),
    ("maltego",         "Visual OSINT link analysis",              "🕸",  "#ef4444", "Recon"),
    ("shodan",          "IoT/internet device search",              "👁",  "#f97316", "Recon"),
    ("dnsenum",         "DNS enumeration & brute-force",           "🌐", "#eab308", "Recon"),
    ("dnsrecon",        "DNS enumeration & zone transfer",         "📡", "#ef4444", "Recon"),
    ("fierce",          "DNS recon & host discovery",              "🦁", "#f97316", "Recon"),
    ("whois",           "Domain registration lookup",              "📋", "#eab308", "Recon"),
    ("enum4linux",      "SMB/NetBIOS enumeration (Linux)",         "🪟", "#ef4444", "Recon"),
    ("enum4linux-ng",   "SMB enumeration rewritten in Python",     "🪟", "#f97316", "Recon"),
    ("netdiscover",     "ARP network scanner",                     "📻", "#eab308", "Recon"),
    ("smbmap",          "SMB share enumeration",                   "📂", "#ef4444", "Recon"),
    ("ldapdomaindump",  "Active Directory LDAP dumper",            "🗄",  "#f97316", "Recon"),
    ("kerbrute",        "Kerberos user enumeration/brute",         "🎫", "#eab308", "Recon"),
    ("fping",           "Fast ICMP host sweeper",                  "📶", "#ef4444", "Recon"),
    ("unicornscan",     "Asynchronous TCP/UDP scanner",            "🦄", "#f97316", "Recon"),
    ("onesixtyone",     "Fast SNMP scanner",                       "📊", "#eab308", "Recon"),
    ("snmpwalk",        "SNMP MIB traversal",                      "🌲", "#ef4444", "Recon"),
    ("dmitry",          "Deep Magic Information Gathering",         "🎩", "#f97316", "Recon"),
    # ── Web Application ────────────────────────────────────────────────────
    ("burpsuite",       "Web proxy, scanner & attack suite",       "🕷",  "#ef4444", "Web"),
    ("sqlmap",          "Automated SQL injection tool",            "🗄",  "#ef4444", "Web"),
    ("nikto",           "Web server vulnerability scanner",        "🌐", "#f97316", "Web"),
    ("gobuster",        "Dir/DNS/vhost brute-force tool",          "📂", "#eab308", "Web"),
    ("feroxbuster",     "Fast recursive content discovery",        "🐾", "#ef4444", "Web"),
    ("ffuf",            "Fast web fuzzer written in Go",           "⚡", "#f97316", "Web"),
    ("wfuzz",           "Web application fuzzer",                  "🌀", "#eab308", "Web"),
    ("dirsearch",       "Web path scanner",                        "🗂",  "#ef4444", "Web"),
    ("whatweb",         "Web fingerprinting tool",                 "🔬", "#f97316", "Web"),
    ("nuclei",          "Template-based vulnerability scanner",    "☢",  "#eab308", "Web"),
    ("dalfox",          "XSS scanner & parameter analysis",        "🦊", "#ef4444", "Web"),
    ("xsstrike",        "Advanced XSS detection suite",            "⚔",  "#f97316", "Web"),
    ("commix",          "Command injection exploiter",             "💥", "#eab308", "Web"),
    ("wpscan",          "WordPress security scanner",              "📰", "#ef4444", "Web"),
    ("joomscan",        "Joomla vulnerability scanner",            "🌴", "#f97316", "Web"),
    ("droopescan",      "CMS vulnerability scanner",               "🌿", "#eab308", "Web"),
    ("wafw00f",         "WAF detection & fingerprinting",          "🧱", "#ef4444", "Web"),
    ("arjun",           "HTTP parameter discovery tool",           "🔧", "#f97316", "Web"),
    ("hakrawler",       "Fast web crawler",                        "🕷",  "#eab308", "Web"),
    ("gau",             "Fetch known URLs from sources",           "🌍", "#ef4444", "Web"),
    ("waybackurls",     "Fetch URLs from Wayback Machine",         "⏳", "#f97316", "Web"),
    ("403fuzzer",       "403 bypass fuzzer",                       "🚧", "#eab308", "Web"),
    ("ssrfmap",         "SSRF detection & exploitation",           "🗺",  "#ef4444", "Web"),
    # ── Exploitation ──────────────────────────────────────────────────────
    ("msfconsole",      "Metasploit penetration testing framework","💉", "#ef4444", "Exploit"),
    ("searchsploit",    "ExploitDB offline search tool",           "📚", "#ef4444", "Exploit"),
    ("beef-xss",        "Browser exploitation framework",          "🐄", "#f97316", "Exploit"),
    ("setoolkit",       "Social engineering toolkit",              "🎭", "#eab308", "Exploit"),
    ("impacket",        "Network protocol attack toolkit",         "📦", "#ef4444", "Exploit"),
    ("responder",       "LLMNR/NBT-NS/MDNS poisoner",             "☠",  "#f97316", "Exploit"),
    ("certipy",         "AD Certificate Services abuse",           "📜", "#eab308", "Exploit"),
    ("evil-winrm",      "WinRM shell for pentesting",              "👿", "#ef4444", "Exploit"),
    ("crackmapexec",    "SMB/WinRM/LDAP network mapper",           "🗺",  "#f97316", "Exploit"),
    ("printspoofer",    "Print Spooler privilege escalation",      "🖨",  "#eab308", "Exploit"),
    ("juicypotato",     "Token impersonation Windows privesc",     "🥤", "#ef4444", "Exploit"),
    ("roguepotato",     "DCOM privesc technique",                  "🥔", "#f97316", "Exploit"),
    ("yersinia",        "Layer 2 protocol attacks (STP/CDP)",      "🦠",  "#eab308", "Exploit"),
    ("heartbleed",      "OpenSSL heartbleed tester",               "💔", "#ef4444", "Exploit"),
    # ── Password Attacks ──────────────────────────────────────────────────
    ("hashcat",         "GPU-accelerated password cracker",        "🔓", "#ef4444", "Passwords"),
    ("john",            "John the Ripper password cracker",        "🔐", "#f97316", "Passwords"),
    ("hydra",           "Network login brute-forcer",              "🔑", "#eab308", "Passwords"),
    ("medusa",          "Parallel network login auditor",          "🐍", "#ef4444", "Passwords"),
    ("cewl",            "Custom wordlist generator from URL",      "📝", "#f97316", "Passwords"),
    ("crunch",          "Wordlist generator",                      "⚙",  "#eab308", "Passwords"),
    ("cupp",            "User password profiler",                  "👤", "#ef4444", "Passwords"),
    ("ophcrack",        "Windows password cracker (rainbow)",      "🌈", "#f97316", "Passwords"),
    ("patator",         "Multi-purpose brute-force tool",          "🔨", "#eab308", "Passwords"),
    ("kerbrute",        "Kerberos password spray & brute-force",   "🎟",  "#ef4444", "Passwords"),
    ("ntlmrelayx",      "NTLM relay attack tool",                  "🔄", "#f97316", "Passwords"),
    ("hashid",          "Hash type identifier",                    "🏷",  "#eab308", "Passwords"),
    ("pypykatz",        "Mimikatz in pure Python",                 "🐍", "#ef4444", "Passwords"),
    ("spray",           "Password spray tool",                     "💧", "#f97316", "Passwords"),
    # ── Network ───────────────────────────────────────────────────────────
    ("netcat",          "TCP/IP swiss army knife",                 "🔌", "#22c55e", "Network"),
    ("ncat",            "Nmap netcat replacement",                 "🔗", "#22c55e", "Network"),
    ("tcpdump",         "CLI packet capture & analysis",           "📡", "#3b82f6", "Network"),
    ("wireshark",       "GUI packet analyzer",                     "📶", "#3b82f6", "Network"),
    ("tshark",          "Terminal-based Wireshark",                "🦈", "#3b82f6", "Network"),
    ("scapy",           "Interactive packet manipulation",         "🐍", "#22c55e", "Network"),
    ("hping3",          "TCP/IP packet generator",                 "🏓", "#ef4444", "Network"),
    ("bettercap",       "MitM attacks & network recon",            "🎯", "#ef4444", "Network"),
    ("ettercap",        "Man-in-the-Middle suite",                 "🕵",  "#ef4444", "Network"),
    ("arpspoof",        "ARP cache poisoning",                     "☠",  "#ef4444", "Network"),
    ("sslstrip",        "HTTPS stripping attack",                  "🔓", "#ef4444", "Network"),
    ("proxychains",     "Proxy chain for TCP apps",                "⛓",  "#eab308", "Network"),
    ("tor",             "Anonymity network client",                "🧅", "#eab308", "Network"),
    ("mitm6",           "IPv6 MitM via DHCPv6",                   "6️⃣", "#ef4444", "Network"),
    ("dnsspoof",        "DNS spoofing tool",                       "🔀", "#f97316", "Network"),
    ("sslscan",         "SSL/TLS scanner",                         "🔒", "#22c55e", "Network"),
    ("testssl",         "Test SSL/TLS quality",                    "🧪", "#22c55e", "Network"),
    ("sslyze",          "TLS/SSL configuration analyzer",          "🔬", "#22c55e", "Network"),
    # ── Wireless ──────────────────────────────────────────────────────────
    ("aircrack-ng",     "WiFi WEP/WPA cracking suite",            "📡", "#eab308", "Wireless"),
    ("airmon-ng",       "Wireless monitor mode manager",           "📻", "#eab308", "Wireless"),
    ("airodump-ng",     "WiFi packet capture",                     "📸", "#ef4444", "Wireless"),
    ("aireplay-ng",     "WiFi packet injection",                   "💥", "#ef4444", "Wireless"),
    ("wifite",          "Automated wireless auditor",              "🤖", "#eab308", "Wireless"),
    ("hostapd-wpe",     "Rogue AP for credential harvest",         "📶", "#ef4444", "Wireless"),
    ("bully",           "WPS brute-force attack",                  "🐂", "#f97316", "Wireless"),
    ("pixiewps",        "Pixie Dust WPS attack",                   "✨", "#eab308", "Wireless"),
    ("reaver",          "WPS PIN attack tool",                     "⛏",  "#ef4444", "Wireless"),
    ("kismet",          "Wireless network detector & sniffer",     "📡", "#f97316", "Wireless"),
    ("mdk4",            "WiFi disruption tool",                    "💣", "#ef4444", "Wireless"),
    ("cowpatty",        "WPA-PSK offline cracker",                 "🐄", "#eab308", "Wireless"),
    # ── Forensics / RE ────────────────────────────────────────────────────
    ("binwalk",         "Firmware analysis & extraction",          "🔍", "#f97316", "Forensics"),
    ("volatility3",     "Memory forensics framework",              "🧠", "#ef4444", "Forensics"),
    ("ghidra",          "NSA reverse engineering suite",           "🐉", "#ef4444", "Forensics"),
    ("radare2",         "Reverse engineering framework",           "🔭", "#f97316", "Forensics"),
    ("gdb",             "GNU debugger (PEDA/pwndbg/gef)",          "🐛", "#eab308", "Forensics"),
    ("strace",          "System call tracer",                      "📊", "#22c55e", "Forensics"),
    ("ltrace",          "Library call tracer",                     "📈", "#22c55e", "Forensics"),
    ("strings",         "Extract printable strings from binary",   "📜", "#eab308", "Forensics"),
    ("exiftool",        "Metadata extraction from files",          "📷", "#f97316", "Forensics"),
    ("foremost",        "File carving & data recovery",            "⛏",  "#ef4444", "Forensics"),
    ("pwntools",        "CTF exploit development library",         "🏴", "#ef4444", "Forensics"),
    ("checksec",        "Binary security property checker",        "🛡",  "#22c55e", "Forensics"),
    ("objdump",         "Object file disassembler",                "🔩", "#eab308", "Forensics"),
    ("yara",            "Malware pattern matching rules",          "🎯", "#ef4444", "Forensics"),
    ("pe-tree",         "PE file viewer/analyzer",                 "🌳", "#f97316", "Forensics"),
    ("file",            "Determine file type",                     "📁", "#22c55e", "Forensics"),
    # ── Post-Exploitation ─────────────────────────────────────────────────
    ("mimikatz",        "Windows credential dumper",               "🔑", "#ef4444", "Post-Exploit"),
    ("bloodhound",      "AD attack path visualizer",               "🐕", "#ef4444", "Post-Exploit"),
    ("neo4j",           "BloodHound graph database backend",       "🗄",  "#f97316", "Post-Exploit"),
    ("chisel",          "TCP/UDP tunnel over HTTP",                "🪓", "#f97316", "Post-Exploit"),
    ("ligolo-ng",       "Advanced tunneling/pivoting agent",       "🌀", "#ef4444", "Post-Exploit"),
    ("pspy",            "Unprivileged Linux process monitor",      "👁",  "#eab308", "Post-Exploit"),
    ("linpeas",         "Linux privilege escalation scanner",      "🐧", "#ef4444", "Post-Exploit"),
    ("winpeas",         "Windows privilege escalation scanner",    "🪟", "#ef4444", "Post-Exploit"),
    ("powercat",        "PowerShell netcat clone",                 "⚡", "#ef4444", "Post-Exploit"),
    ("smbexec",         "SMB command execution",                   "💻", "#f97316", "Post-Exploit"),
    ("psexec",          "Impacket PsExec implementation",          "🖥",  "#eab308", "Post-Exploit"),
    ("wmiexec",         "WMI command execution",                   "🖱",  "#ef4444", "Post-Exploit"),
    ("secretsdump",     "Remote SAM/NTDS.dit dumper",              "🔓", "#f97316", "Post-Exploit"),
    ("ticketer",        "Kerberos silver/golden ticket creator",   "🎫", "#eab308", "Post-Exploit"),
    ("lsassy",          "Remote LSASS dump & parse",               "💾", "#ef4444", "Post-Exploit"),
]

BLUE_TOOLS: list[tuple[str, str, str, str, str]] = [
    # ── Network Monitoring ────────────────────────────────────────────────
    ("wireshark",       "GUI packet capture & analysis",           "📶", "#3b82f6", "Monitoring"),
    ("tshark",          "CLI packet capture & analysis",           "🦈", "#3b82f6", "Monitoring"),
    ("tcpdump",         "Lightweight command-line sniffer",        "📡", "#22c55e", "Monitoring"),
    ("zeek",            "Network security monitor & analyzer",     "🦓", "#3b82f6", "Monitoring"),
    ("arkime",          "Full PCAP capture, index & search",       "🌊", "#3b82f6", "Monitoring"),
    ("ntopng",          "Network traffic flow monitor",            "📊", "#22c55e", "Monitoring"),
    ("iftop",           "Bandwidth usage per connection",          "📈", "#22c55e", "Monitoring"),
    ("nethogs",         "Per-process network bandwidth",           "🐷", "#3b82f6", "Monitoring"),
    ("iptraf-ng",       "Interactive IP traffic monitor",          "🖥",  "#22c55e", "Monitoring"),
    ("ss",              "Socket statistics (modern netstat)",      "🔌", "#22c55e", "Monitoring"),
    ("netstat",         "Network connections & routing table",     "🗺",  "#3b82f6", "Monitoring"),
    ("darkstat",        "Network statistics web interface",        "🌑", "#22c55e", "Monitoring"),
    ("bandwhich",       "Terminal bandwidth utilization tool",     "📡", "#3b82f6", "Monitoring"),
    ("vnstat",          "Network traffic statistics logger",       "📋", "#22c55e", "Monitoring"),
    ("nload",           "Real-time bandwidth monitor",             "📉", "#3b82f6", "Monitoring"),
    ("pmacct",          "Passive network monitoring suite",        "📦", "#22c55e", "Monitoring"),
    # ── IDS / IPS ─────────────────────────────────────────────────────────
    ("suricata",        "High-perf IDS/IPS/NSM engine",           "🛡",  "#3b82f6", "IDS/IPS"),
    ("snort",           "Network intrusion detection system",      "👃", "#3b82f6", "IDS/IPS"),
    ("ossec",           "Host-based intrusion detection (HIDS)",   "🏠", "#22c55e", "IDS/IPS"),
    ("wazuh",           "SIEM + XDR security platform",           "🔐", "#3b82f6", "IDS/IPS"),
    ("aide",            "Advanced intrusion detection env",        "📋", "#22c55e", "IDS/IPS"),
    ("samhain",         "File integrity & HIDS system",            "🔮", "#3b82f6", "IDS/IPS"),
    ("fail2ban",        "Log-based intrusion prevention",          "🚫", "#22c55e", "IDS/IPS"),
    ("psad",            "Port scan attack detector",               "🎯", "#3b82f6", "IDS/IPS"),
    ("tripwire",        "File integrity monitoring system",        "🕸",  "#22c55e", "IDS/IPS"),
    ("denyhosts",       "SSH brute-force prevention",              "🚷", "#3b82f6", "IDS/IPS"),
    ("sshguard",        "SSH & service brute-force guard",         "💂", "#22c55e", "IDS/IPS"),
    ("crowdsec",        "Open-source crowdsourced IPS",            "👥", "#3b82f6", "IDS/IPS"),
    ("modsecurity",     "Open-source web application firewall",    "🧱", "#22c55e", "IDS/IPS"),
    ("fwknop",          "Single packet authorization firewall",    "🔒", "#3b82f6", "IDS/IPS"),
    # ── Vulnerability Scanning ─────────────────────────────────────────────
    ("openvas",         "Full vulnerability scanner (GVM)",        "🩺", "#3b82f6", "Scanning"),
    ("nessus",          "Tenable Nessus vulnerability scanner",    "🔬", "#3b82f6", "Scanning"),
    ("nmap",            "Port scan + NSE script engine",           "🔍", "#22c55e", "Scanning"),
    ("nuclei",          "Template-based vuln scanner",             "☢",  "#3b82f6", "Scanning"),
    ("lynis",           "Security auditing & hardening guide",     "🔎", "#22c55e", "Scanning"),
    ("grype",           "Container image vulnerability scanner",   "📦", "#3b82f6", "Scanning"),
    ("trivy",           "Container & FS vulnerability scanner",    "🔭", "#22c55e", "Scanning"),
    ("prowler",         "AWS/GCP/Azure security assessment",       "☁",  "#3b82f6", "Scanning"),
    ("cve-search",      "CVE lookup & analysis tool",              "📚", "#22c55e", "Scanning"),
    ("vulmap",          "Online local exploit suggester",          "🗺",  "#3b82f6", "Scanning"),
    ("dockle",          "Container image security linter",         "🐳", "#22c55e", "Scanning"),
    ("kube-bench",      "CIS Kubernetes benchmark checker",        "☸",  "#3b82f6", "Scanning"),
    ("checkov",         "IaC static analysis tool",                "✅", "#22c55e", "Scanning"),
    ("scoutsuite",      "Multi-cloud security audit tool",         "🌐", "#3b82f6", "Scanning"),
    ("greenbone",       "Greenbone vulnerability manager",         "🟢", "#22c55e", "Scanning"),
    # ── System Hardening ──────────────────────────────────────────────────
    ("auditd",          "Linux kernel audit daemon",               "📋", "#22c55e", "Hardening"),
    ("apparmor",        "Mandatory access control (MAC)",          "🔒", "#22c55e", "Hardening"),
    ("selinux",         "Security-Enhanced Linux policy",          "🛡",  "#3b82f6", "Hardening"),
    ("ufw",             "Uncomplicated firewall",                  "🔥", "#22c55e", "Hardening"),
    ("iptables",        "Netfilter packet filtering",              "⛓",  "#3b82f6", "Hardening"),
    ("nftables",        "Next-gen Linux firewall framework",       "🔥", "#22c55e", "Hardening"),
    ("chkrootkit",      "Classic rootkit scanner",                 "🔦", "#22c55e", "Hardening"),
    ("rkhunter",        "Rootkit, backdoor & exploit scanner",     "🕵",  "#22c55e", "Hardening"),
    ("tiger",           "UNIX security audit & IDS",               "🐯", "#3b82f6", "Hardening"),
    ("bastille",        "Linux hardening automation",              "🏰", "#22c55e", "Hardening"),
    ("cryptsetup",      "LUKS disk encryption management",         "🔐", "#22c55e", "Hardening"),
    ("firejail",        "Application sandboxing with namespaces",  "🏖",  "#3b82f6", "Hardening"),
    ("debsums",         "Verify Debian package file integrity",    "✅", "#22c55e", "Hardening"),
    ("age",             "Modern file encryption tool",             "🔒", "#3b82f6", "Hardening"),
    ("pass",            "GPG-encrypted password store",            "🔑", "#22c55e", "Hardening"),
    ("yubikey-manager", "YubiKey 2FA configuration tool",          "🗝",  "#3b82f6", "Hardening"),
    # ── Malware Analysis ──────────────────────────────────────────────────
    ("clamav",          "Open-source antivirus engine",            "🦠",  "#3b82f6", "Malware"),
    ("yara",            "Malware identification & classification", "🎯", "#ef4444", "Malware"),
    ("volatility3",     "Memory forensics & malware analysis",     "🧠", "#ef4444", "Malware"),
    ("ghidra",          "NSA malware reverse engineering",         "🐉", "#ef4444", "Malware"),
    ("radare2",         "Binary analysis & reverse engineering",   "🔭", "#f97316", "Malware"),
    ("cuckoo",          "Automated malware sandbox analysis",      "🐦", "#ef4444", "Malware"),
    ("binwalk",         "Firmware analysis & extraction",          "🔍", "#f97316", "Malware"),
    ("strings",         "Extract printable strings from binary",   "📜", "#22c55e", "Malware"),
    ("exiftool",        "File metadata extraction",                "📷", "#22c55e", "Malware"),
    ("maldet",          "Linux malware detect (LMD)",              "🔎", "#ef4444", "Malware"),
    ("loki",            "IOC & YARA scanner",                      "⚡", "#ef4444", "Malware"),
    ("fenrir",          "Simple IOC checker (bash-based)",         "🦊", "#f97316", "Malware"),
    ("cape",            "CAPE sandbox for malware analysis",       "🎭", "#ef4444", "Malware"),
    ("strace",          "System call tracer for analysis",         "📊", "#22c55e", "Malware"),
    # ── Log Analysis / SIEM ───────────────────────────────────────────────
    ("elk",             "Elasticsearch + Logstash + Kibana",       "🔎", "#3b82f6", "SIEM"),
    ("graylog",         "Log management platform",                 "📊", "#3b82f6", "SIEM"),
    ("loki",            "Grafana log aggregation system",          "🗂",  "#22c55e", "SIEM"),
    ("grafana",         "Metrics & log visualization",             "📈", "#f97316", "SIEM"),
    ("splunk",          "Security data analytics platform",        "🔮", "#3b82f6", "SIEM"),
    ("chainsaw",        "Windows event log analyzer",              "⛓",  "#22c55e", "SIEM"),
    ("sigma",           "Generic SIEM detection rule format",      "Σ",  "#3b82f6", "SIEM"),
    ("timesketch",      "Collaborative timeline analysis",         "⏱",  "#22c55e", "SIEM"),
    ("velociraptor",    "DFIR endpoint visibility platform",       "🦖", "#3b82f6", "SIEM"),
    ("fluentd",         "Log data collector & forwarder",          "💧", "#22c55e", "SIEM"),
    ("logstash",        "Server-side data processing pipeline",    "🔄", "#3b82f6", "SIEM"),
    ("opensearch",      "Open-source Elasticsearch fork",          "🔍", "#22c55e", "SIEM"),
    # ── Digital Forensics ─────────────────────────────────────────────────
    ("autopsy",         "Digital forensics investigation platform","🔬", "#f97316", "Forensics"),
    ("sleuthkit",       "Filesystem forensics toolkit (TSK)",      "🔍", "#22c55e", "Forensics"),
    ("foremost",        "File carving & recovery tool",            "⛏",  "#f97316", "Forensics"),
    ("photorec",        "File recovery from disk & memory",        "📸", "#22c55e", "Forensics"),
    ("dd",              "Raw disk image creation",                 "💿", "#22c55e", "Forensics"),
    ("dc3dd",           "Forensic disk copy with hashing",         "🔐", "#22c55e", "Forensics"),
    ("testdisk",        "Partition recovery tool",                 "💾", "#3b82f6", "Forensics"),
    ("bulk_extractor",  "Bulk data extraction from disk images",   "📦", "#22c55e", "Forensics"),
    ("plaso",           "Log2Timeline super-timeline tool",        "⏰", "#3b82f6", "Forensics"),
    ("regripper",       "Windows registry forensics tool",         "🗃",  "#f97316", "Forensics"),
    ("fdisk",           "Disk partition management tool",          "💽", "#22c55e", "Forensics"),
    # ── Compliance / Audit ────────────────────────────────────────────────
    ("openscap",        "SCAP compliance scanner & enforcer",      "📋", "#3b82f6", "Compliance"),
    ("inspec",          "Compliance-as-code testing framework",    "✅", "#22c55e", "Compliance"),
    ("prowler",         "CIS benchmark cloud compliance check",    "🎖",  "#22c55e", "Compliance"),
    ("kube-bench",      "CIS Kubernetes security benchmark",       "☸",  "#3b82f6", "Compliance"),
    ("lynis",           "CIS benchmark system audit",              "🔎", "#22c55e", "Compliance"),
    ("conftest",        "Policy testing for config files",         "📝", "#3b82f6", "Compliance"),
    ("terrascan",       "IaC security scanner (Terraform/K8s)",    "🌍", "#22c55e", "Compliance"),
    ("tfsec",           "Terraform security scanner",              "🔒", "#3b82f6", "Compliance"),
    ("checkov",         "Policy-as-code IaC scanner",              "✔",  "#22c55e", "Compliance"),
    ("vuls",            "Linux/FreeBSD vulnerability scanner",     "🕵",  "#3b82f6", "Compliance"),
    ("tiger",           "UNIX security compliance audit",          "🐯", "#22c55e", "Compliance"),
]

# ── Widgets ─────────────────────────────────────────────────────────────────

CARD_COLORS = {
    "#ef4444": ("#ef444415", "#ef444440"),  # red
    "#f97316": ("#f9731615", "#f9731640"),  # orange
    "#eab308": ("#eab30815", "#eab30840"),  # yellow
    "#22c55e": ("#22c55e15", "#22c55e40"),  # green
    "#3b82f6": ("#3b82f615", "#3b82f640"),  # blue
}


class ToolCard(QFrame):
    def __init__(self, name: str, desc: str, icon: str, color: str,
                 category: str, ipc):
        super().__init__()
        self.setObjectName("toolCard")
        self.setFixedHeight(88)
        self._name     = name
        self._category = category
        self._color    = color
        self._ipc      = ipc

        bg, border = CARD_COLORS.get(color, ("#ffffff08", "#ffffff20"))
        self.setStyleSheet(f"""
            QFrame#toolCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QFrame#toolCard:hover {{
                background: {color}20;
                border: 1px solid {color}60;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        # Top row: icon + name + category badge + run button
        top = QHBoxLayout()
        top.setSpacing(6)

        lbl_icon = QLabel(icon)
        lbl_icon.setFixedWidth(22)
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent;")
        top.addWidget(lbl_icon)

        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 700; "
            "font-family: 'JetBrains Mono', 'Fira Code', monospace; "
            "background: transparent;"
        )
        top.addWidget(lbl_name)
        top.addStretch()

        # Category badge
        lbl_cat = QLabel(category)
        lbl_cat.setStyleSheet(
            f"color: {color}bb; font-size: 9px; font-weight: 700; "
            f"background: {color}18; border: 1px solid {color}35; "
            "border-radius: 3px; padding: 1px 6px; letter-spacing: 0.5px;"
        )
        top.addWidget(lbl_cat)

        btn_run = QPushButton("▶")
        btn_run.setFixedSize(26, 22)
        btn_run.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_run.setStyleSheet(
            f"QPushButton {{ background: {color}28; border: 1px solid {color}55; "
            f"color: {color}; border-radius: 4px; font-size: 11px; margin-left: 4px; }}"
            f"QPushButton:hover {{ background: {color}50; border-color: {color}; }}"
            f"QPushButton:pressed {{ background: {color}70; }}"
        )
        btn_run.clicked.connect(self._launch)
        btn_run.setToolTip(f"Run {name} in terminal")
        top.addWidget(btn_run)
        layout.addLayout(top)

        # Description
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(
            "color: #5a5a6a; font-size: 11px; background: transparent;"
        )
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

    def _launch(self):
        if self._ipc:
            self._ipc.call_async(
                "container_exec",
                {"cmd": self._name},
                lambda _: None
            )


class ContainerStatusBar(QFrame):
    """Slim top status bar showing container state."""
    def __init__(self, ipc):
        super().__init__()
        self._ipc = ipc
        self.setFixedHeight(44)
        self.setStyleSheet(
            "QFrame { background: #161618; border: 1px solid #2a2a32; border-radius: 6px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(12)

        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #3a3a3a; font-size: 12px;")
        layout.addWidget(self._dot)

        self._lbl = QLabel("Checking container…")
        self._lbl.setStyleSheet("color: #555; font-size: 12px; font-family: 'JetBrains Mono', monospace;")
        layout.addWidget(self._lbl)

        layout.addStretch()

        self._lbl_engine = QLabel("podman")
        self._lbl_engine.setStyleSheet(
            "color: #444; font-size: 10px; font-family: monospace; "
            "background: #1e1e22; border: 1px solid #2a2a32; "
            "border-radius: 3px; padding: 2px 8px;"
        )
        layout.addWidget(self._lbl_engine)

        self._btn = QPushButton("Start Container")
        self._btn.setFixedHeight(28)
        self._btn.setStyleSheet(
            "QPushButton { background: #1e2a1e; border: 1px solid #22c55e44; "
            "color: #22c55e; font-size: 11px; font-weight: 700; "
            "border-radius: 4px; padding: 0 12px; }"
            "QPushButton:hover { background: #22c55e22; border-color: #22c55e88; }"
        )
        self._btn.clicked.connect(self._toggle)
        layout.addWidget(self._btn)

        self._running = False
        QTimer.singleShot(600, self._refresh)

    def _refresh(self):
        if self._ipc:
            self._ipc.call_async("container_status", {}, self._on_status)

    def _on_status(self, result):
        if result and result.get("running"):
            self._running = True
            self._dot.setStyleSheet("color: #22c55e; font-size: 12px;")
            self._lbl.setText("cybersec-mode-env  ─  running  ─  blackarchlinux/blackarch")
            self._lbl.setStyleSheet("color: #aaa; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
            self._btn.setText("Stop")
            self._btn.setStyleSheet(
                "QPushButton { background: #2a1e1e; border: 1px solid #ef444444; "
                "color: #ef4444; font-size: 11px; font-weight: 700; "
                "border-radius: 4px; padding: 0 12px; }"
                "QPushButton:hover { background: #ef444422; }"
            )
            engine = result.get("engine", "podman")
            self._lbl_engine.setText(engine)
        else:
            self._running = False
            self._dot.setStyleSheet("color: #ef4444; font-size: 12px;")
            self._lbl.setText("Container stopped  ─  click Start to launch BlackArch environment")
            self._lbl.setStyleSheet("color: #666; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
            self._btn.setText("Start Container")
            self._btn.setStyleSheet(
                "QPushButton { background: #1e2a1e; border: 1px solid #22c55e44; "
                "color: #22c55e; font-size: 11px; font-weight: 700; "
                "border-radius: 4px; padding: 0 12px; }"
                "QPushButton:hover { background: #22c55e22; }"
            )

    def _toggle(self):
        if self._running:
            if self._ipc:
                self._ipc.call_async("container_stop", {"name": "cybersec-mode-env"},
                                     lambda _: QTimer.singleShot(500, self._refresh))
        else:
            if self._ipc:
                self._ipc.call_async(
                    "container_start",
                    {"image": "blackarchlinux/blackarch", "name": "cybersec-mode-env"},
                    lambda _: QTimer.singleShot(1000, self._refresh)
                )


class CategoryBar(QFrame):
    """Horizontal scrollable category filter buttons."""
    def __init__(self, categories: list[str], mode: str, on_select):
        super().__init__()
        self.setFixedHeight(36)
        self.setStyleSheet("QFrame { background: transparent; }")
        self._on_select = on_select
        self._mode      = mode
        self._active    = "All"
        self._buttons: dict[str, QPushButton] = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        for cat in categories:
            btn = QPushButton(cat)
            btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda _, c=cat: self._click(c))
            layout.addWidget(btn)
            self._buttons[cat] = btn

        layout.addStretch()
        self._refresh_styles()

    def _click(self, cat: str):
        self._active = cat
        self._refresh_styles()
        self._on_select(cat)

    def _refresh_styles(self):
        accent = "#ef4444" if self._mode == "red" else "#3b82f6"
        for cat, btn in self._buttons.items():
            if cat == self._active:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}22; border: 1px solid {accent}66; "
                    f"color: {accent}; border-radius: 4px; padding: 0 10px; "
                    f"font-size: 11px; font-weight: 700; }}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background: transparent; border: 1px solid #2a2a32; "
                    "color: #555; border-radius: 4px; padding: 0 10px; font-size: 11px; }"
                    "QPushButton:hover { background: #1e1e22; color: #aaa; border-color: #3a3a44; }"
                )

    def reset(self, categories: list[str], mode: str):
        self._mode   = mode
        self._active = "All"
        # Update button list without full rebuild (caller should rebuild instead)


class MainPanel(QWidget):
    def __init__(self, config, ipc):
        super().__init__()
        self._config     = config
        self._ipc        = ipc
        self._active_cat = "All"
        self._cat_bar: CategoryBar | None = None
        self._build()

    # ── Categories ────────────────────────────────────────────────────────

    def _get_tools(self) -> list[tuple]:
        mode = self._config.get("mode", "red")
        return RED_TOOLS if mode == "red" else BLUE_TOOLS

    def _get_categories(self) -> list[str]:
        return ["All"] + list(dict.fromkeys(t[4] for t in self._get_tools()))

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        self._lbl_title = QLabel()
        self._update_title()
        hdr.addWidget(self._lbl_title)
        hdr.addStretch()

        # Stats
        self._lbl_stats = QLabel()
        self._lbl_stats.setStyleSheet("color: #3a3a4a; font-size: 11px; font-family: monospace;")
        hdr.addWidget(self._lbl_stats)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("  Search tools…")
        self._search.setFixedWidth(190)
        self._search.setFixedHeight(30)
        self._search.setStyleSheet(
            "QLineEdit { background: #161618; border: 1px solid #2a2a32; "
            "color: #ccc; border-radius: 5px; font-size: 12px; padding: 0 8px; }"
            "QLineEdit:focus { border-color: #444; }"
        )
        self._search.textChanged.connect(self._filter)
        hdr.addWidget(self._search)
        layout.addLayout(hdr)

        # Container status
        self._status_bar = ContainerStatusBar(self._ipc)
        layout.addWidget(self._status_bar)

        # Category bar placeholder — rebuilt on mode change
        self._cat_frame = QWidget()
        self._cat_layout = QHBoxLayout(self._cat_frame)
        self._cat_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_layout.setSpacing(6)
        layout.addWidget(self._cat_frame)

        # Scroll area for tool cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(8)
        self._grid.setContentsMargins(0, 4, 0, 4)
        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll)

        self._cards: list[ToolCard] = []
        self._populate()

    # ── Populate ──────────────────────────────────────────────────────────

    def _clear_cat_bar(self):
        while self._cat_layout.count():
            item = self._cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _build_cat_bar(self):
        self._clear_cat_bar()
        mode   = self._config.get("mode", "red")
        accent = "#ef4444" if mode == "red" else "#3b82f6"
        cats   = self._get_categories()

        for cat in cats:
            btn = QPushButton(cat)
            btn.setFixedHeight(28)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            is_active = cat == self._active_cat
            if is_active:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}22; border: 1px solid {accent}66; "
                    f"color: {accent}; border-radius: 4px; padding: 0 10px; "
                    f"font-size: 11px; font-weight: 700; }}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background: transparent; border: 1px solid #2a2a32; "
                    "color: #555; border-radius: 4px; padding: 0 10px; font-size: 11px; }"
                    "QPushButton:hover { background: #1e1e22; color: #aaa; }"
                )
            btn.clicked.connect(lambda _, c=cat: self._set_category(c))
            self._cat_layout.addWidget(btn)

        self._cat_layout.addStretch()

    def _set_category(self, cat: str):
        self._active_cat = cat
        self._build_cat_bar()
        self._filter(self._search.text())

    def _populate(self):
        for c in self._cards:
            c.deleteLater()
        self._cards.clear()

        tools = self._get_tools()
        COLS  = 3

        for i, (name, desc, icon, color, category) in enumerate(tools):
            card = ToolCard(name, desc, icon, color, category, self._ipc)
            self._grid.addWidget(card, i // COLS, i % COLS)
            self._cards.append(card)

        self._active_cat = "All"
        self._build_cat_bar()
        self._update_stats(len(tools), len(tools))

    def _filter(self, text: str):
        text   = text.lower().strip()
        COLS   = 3
        row, col = 0, 0
        visible  = 0

        for card in self._cards:
            cat_ok  = self._active_cat == "All" or card._category == self._active_cat
            text_ok = not text or text in card._name.lower() or text in card._category.lower()
            show    = cat_ok and text_ok
            card.setVisible(show)

            if show:
                self._grid.removeWidget(card)
                self._grid.addWidget(card, row, col)
                col += 1
                if col >= COLS:
                    col = 0
                    row += 1
                visible += 1

        self._update_stats(visible, len(self._cards))

    def _update_stats(self, visible: int, total: int):
        mode = self._config.get("mode", "red")
        icon = "⚔" if mode == "red" else "🛡"
        self._lbl_stats.setText(f"{icon}  {visible} / {total} tools")

    def _update_title(self):
        mode = self._config.get("mode", "red")
        if mode == "red":
            self._lbl_title.setText("⚔  Offensive / Pentest")
            self._lbl_title.setStyleSheet(
                "font-size: 16px; font-weight: 800; color: #ef4444; letter-spacing: -0.5px;"
            )
        else:
            self._lbl_title.setText("🛡  Defensive / Audit")
            self._lbl_title.setStyleSheet(
                "font-size: 16px; font-weight: 800; color: #3b82f6; letter-spacing: -0.5px;"
            )

    @pyqtSlot(str)
    def on_mode_changed(self, mode: str):
        self._update_title()
        self._populate()
