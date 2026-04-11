require "option_parser"
require "json"
require "process"
require "colorize"

VERSION     = "0.1"
APP_NAME    = "Cybersecurity Mode"
GUI_BIN     = "/usr/lib/HackerOS/Cybersecurity-Mode/cybersec-mode-main"
BACKEND_BIN = "/usr/lib/HackerOS/Cybersecurity-Mode/cybersec-mode-backend"
CAGE_BIN    = "/usr/bin/cage"
HSH_BIN     = "/usr/bin/hsh"
CACHE_DIR   = "#{Path.home}/.cache/HackerOS/Cybersecurity-Mode"
CONFIG_FILE = "#{CACHE_DIR}/config.json"
PLUGIN_DIR  = "#{CACHE_DIR}/plugins"
LOG_DIR     = "#{Path.home}/.local/share/HackerOS/Cybersecurity-Mode/logs"

def red(text)    : String; text.colorize(:red).to_s       end
def green(text)  : String; text.colorize(:green).to_s     end
def yellow(text) : String; text.colorize(:yellow).to_s    end
def cyan(text)   : String; text.colorize(:cyan).to_s      end
def bold(text)   : String; text.colorize.bold.to_s        end
def dim(text)    : String; text.colorize(:dark_gray).to_s end

# Replaces deprecated File.executable? — use File::Info permissions
def executable?(path : String) : Bool
  return false unless File.exists?(path)
  info = File.info(path)
  info.permissions.owner_execute? ||
  info.permissions.group_execute? ||
  info.permissions.other_execute?
rescue
  false
end

def banner
  puts ""
  puts cyan("  ╔══════════════════════════════════════════════════╗")
  puts "  #{cyan("║")}  #{bold("⚡ Cybersecurity Mode")}  #{dim("v#{VERSION}")}  #{cyan("│")}  #{bold("HackerOS")}        #{cyan("║")}"
  puts cyan("  ╚══════════════════════════════════════════════════╝")
  puts ""
end

def config_get(key : String) : String?
  return nil unless File.exists?(CONFIG_FILE)
  JSON.parse(File.read(CONFIG_FILE))[key]?.try(&.as_s?)
rescue
  nil
end

def config_set(key : String, value : String)
  Dir.mkdir_p(CACHE_DIR)
  data = if File.exists?(CONFIG_FILE)
    begin; JSON.parse(File.read(CONFIG_FILE)).as_h; rescue; {} of String => JSON::Any; end
  else
    {} of String => JSON::Any
  end
  data[key] = JSON::Any.new(value)
  File.write(CONFIG_FILE, data.to_json)
rescue ex
  STDERR.puts red("Config write error: #{ex.message}")
end

def in_tty? : Bool
  STDIN.tty? && STDOUT.tty?
end

def require_tty!
  unless in_tty?
    puts red("  ✗  This command requires a TTY.")
    puts dim("     Launch from a real terminal, not inside the GUI.")
    exit 1
  end
end

def detect_engine : String
  executable?("/usr/bin/podman") ? "podman" : "docker"
end

def cmd_launch_session
  require_tty!
  unless executable?(GUI_BIN)
    puts red("  ✗  GUI binary not found: #{GUI_BIN}")
    puts dim("     Run: sudo bash install.sh")
    exit 1
  end
  banner
  puts "  " + green("▶") + "  Launching Cybersecurity Mode session…"
  shell = executable?(HSH_BIN) ? HSH_BIN : "/bin/bash"
  puts "  " + dim("Shell: #{shell}")
  puts ""
  env = {
    "XDG_SESSION_TYPE" => "wayland",
    "CYBERSEC_SESSION" => "1",
    "CYBERSEC_VERSION" => VERSION,
    "CYBERSEC_SHELL"   => shell,
  }
  if executable?(CAGE_BIN)
    Process.exec(CAGE_BIN, [GUI_BIN], env: env)
  else
    puts "  " + yellow("⚠") + "  cage not found — launching without Wayland compositor"
    Process.exec(GUI_BIN, env: env)
  end
end

def cmd_launch_in_session
  unless executable?(GUI_BIN)
    puts red("  ✗  Binary not found: #{GUI_BIN}")
    exit 1
  end
  shell = executable?(HSH_BIN) ? HSH_BIN : "/bin/bash"
  env = {
    "CYBERSEC_SESSION" => "0",
    "CYBERSEC_VERSION" => VERSION,
    "CYBERSEC_SHELL"   => shell,
  }
  puts "  " + green("▶") + "  Launching GUI in current session…"
  Process.exec(GUI_BIN, env: env)
end

def cmd_help
  banner
  puts bold("  USAGE")
  puts "    #{cyan("cybersec")}                  Launch session (TTY only)"
  puts "    #{cyan("cybersec please")}           Launch GUI in existing session"
  puts "    #{cyan("cybersec help")}             Show this help"
  puts "    #{cyan("cybersec version")}          Print version"
  puts "    #{cyan("cybersec status")}           System & container status"
  puts "    #{cyan("cybersec update")}           Update app + container"
  puts "    #{cyan("cybersec set-mode")} MODE    Set mode: #{red("red")} | #{cyan("blue")}"
  puts "    #{cyan("cybersec exec")} CMD         Run command in container"
  puts "    #{cyan("cybersec shell")}            Open hsh shell in container"
  puts "    #{cyan("cybersec container")} CMD    Container: start|stop|rm|logs"
  puts "    #{cyan("cybersec plugin")} CMD       Plugins: list|install|remove|info"
  puts "    #{cyan("cybersec tools")} [CAT]      List security tools"
  puts "    #{cyan("cybersec back")}             Switch back to Cybersec Mode session (tty3)"
  puts "    #{cyan("cybersec back kde")}         Switch back to KDE Plasma (tty2)"
  puts ""
  puts bold("  EXAMPLES")
  puts "    #{dim("# Full TTY session (from Ctrl+Alt+F2)")}"
  puts "    cybersec"
  puts "    #{dim("# Open GUI inside KDE/GNOME")}"
  puts "    cybersec please"
  puts "    #{dim("# Run nmap in container")}"
  puts "    cybersec exec 'nmap -sV 192.168.1.0/24'"
  puts "    #{dim("# Open hsh shell")}"
  puts "    cybersec shell"
  puts "    #{dim("# Switch to blue mode")}"
  puts "    cybersec set-mode blue"
  puts "    #{dim("# See all tools")}"
  puts "    cybersec tools"
  puts ""
  puts "  #{bold("Paths")}"
  puts "    Cache   #{dim(CACHE_DIR)}"
  puts "    Logs    #{dim(LOG_DIR)}"
  puts "    Shell   #{dim(executable?(HSH_BIN) ? HSH_BIN : "/bin/bash (hsh not found)")}"
  puts ""
end

def cmd_update
  banner
  puts bold("  ⬆  Updating Cybersecurity Mode v#{VERSION}…")
  puts "  " + dim("─" * 50)
  puts ""
  steps = [
    {"App update check (placeholder)",
     ["echo", "[v#{VERSION}] Managed by HackerOS package manager"]},
    {"Pull latest BlackArch image",
     ["podman", "pull", "blackarchlinux/blackarch"]},
    {"Update keyring in container",
     ["podman", "exec", "cybersec-mode-env", "bash", "-c",
      "pacman -Sy --noconfirm blackarch-keyring 2>/dev/null || echo '[skip]'"]},
    {"Upgrade container packages",
     ["podman", "exec", "cybersec-mode-env", "bash", "-c",
      "pacman -Syu --noconfirm 2>/dev/null || echo '[skip]'"]},
    {"Check hsh shell",
     ["bash", "-c",
      "[ -x /usr/bin/hsh ] && echo '[ok] hsh ready' || echo '[skip] hsh not installed'"]},
  ]
  steps.each_with_index do |(label, cmd), i|
    puts "  #{cyan("[#{i+1}/#{steps.size}]")} #{label}"
    Process.run(cmd[0], cmd[1..], output: STDOUT, error: STDERR)
    puts ""
  end
  puts "  " + green("✓") + "  Update complete."
  puts ""
end

def cmd_plugin(args : Array(String))
  sub = args.first? || "list"
  case sub
  when "list"
    Dir.mkdir_p(PLUGIN_DIR)
    plugins = Dir.glob("#{PLUGIN_DIR}/*.json").map do |f|
      JSON.parse(File.read(f))["name"]?.try(&.as_s?) || File.basename(f, ".json")
    end
    if plugins.empty?
      puts dim("  No plugins installed.  cybersec plugin install <n>")
    else
      puts bold("  Installed plugins:")
      plugins.each { |p| puts "    #{cyan("▸")} #{p}" }
    end
  when "install"
    name = args[1]?
    if name.nil?; puts red("  ✗  Usage: cybersec plugin install <n>"); exit 1; end
    puts yellow("  ⚠  Plugin system placeholder — coming in v0.2")
  when "remove"
    name = args[1]?
    if name.nil?; puts red("  ✗  Usage: cybersec plugin remove <n>"); exit 1; end
    pf = "#{PLUGIN_DIR}/#{name}.json"
    if File.exists?(pf)
      File.delete(pf); puts green("  ✓  Removed '#{name}'.")
    else
      puts red("  ✗  Plugin '#{name}' not installed.")
    end
  when "info"
    name = args[1]?
    if name.nil?; puts red("  ✗  Usage: cybersec plugin info <n>"); exit 1; end
    pf = "#{PLUGIN_DIR}/#{name}.json"
    puts File.exists?(pf) ? File.read(pf) : red("  ✗  Not found.")
  else
    puts red("  ✗  Unknown: #{sub}  —  list|install|remove|info")
  end
end

def cmd_status
  banner
  engine = detect_engine
  puts bold("  ◉  System Status")
  puts "  " + dim("─" * 44)
  puts ""
  puts "  #{bold("Binaries")}"
  {
    "GUI (cybersec-mode-main)"    => GUI_BIN,
    "Backend (cybersec-backend)"  => BACKEND_BIN,
    "CLI (/usr/bin/cybersec)"     => "/usr/bin/cybersec",
    "Shell (/usr/bin/hsh)"        => HSH_BIN,
    "Cage (Wayland compositor)"   => CAGE_BIN,
  }.each do |label, path|
    ok  = executable?(path)
    sym = ok ? green("✓") : red("✗")
    puts "    #{sym}  #{label.ljust(32)} #{dim(path)}"
  end
  puts ""
  puts "  #{bold("Container")}"
  puts "    Engine:  #{cyan(engine)}"
  state_out = ""
  Process.run(engine,
    ["inspect", "--format", "{{.State.Status}}", "cybersec-mode-env"],
    output: Process::Redirect::Pipe, error: Process::Redirect::Close
  ) { |p| state_out = p.output.gets_to_end.strip }
  state = state_out.empty? ? "not found" : state_out
  col   = state == "running" ? :green : :red
  puts "    Status:  #{state.colorize(col)}"
  puts ""
  puts "  #{bold("Configuration")}"
  mode = config_get("mode") || "not set"
  mc   = mode == "red" ? :red : :cyan
  puts "    Mode:    #{mode.colorize(mc)}"
  puts "    Config:  #{dim(CONFIG_FILE)}"
  puts "    Cache:   #{dim(CACHE_DIR)}"
  puts "    Logs:    #{dim(LOG_DIR)}"
  puts ""
  puts "  #{bold("Version:")} #{cyan("v#{VERSION}")}  —  HackerOS Cybersecurity Mode"
  puts ""
end

def cmd_set_mode(args : Array(String))
  mode = args.first?
  unless mode == "red" || mode == "blue"
    puts red("  ✗  Invalid mode. Use: #{red("red")} | #{cyan("blue")}")
    exit 1
  end
  mode_str = mode.not_nil!
  config_set("mode", mode_str)
  col = mode_str == "red" ? :red : :cyan
  puts "  " + green("✓") + "  Mode set to #{mode_str.colorize(col)}."
end

def cmd_exec(args : Array(String))
  cmd_str = args.join(" ")
  if cmd_str.empty?
    puts red("  ✗  Usage: cybersec exec <command>")
    exit 1
  end
  Process.exec(detect_engine, ["exec", "-it", "cybersec-mode-env", "bash", "-c", cmd_str])
end

def cmd_shell
  engine = detect_engine
  shell  = executable?(HSH_BIN) ? HSH_BIN : "/bin/bash"
  puts "  " + green("▶") + "  Opening #{dim(shell)} in container…"
  Process.exec(engine, ["exec", "-it", "cybersec-mode-env", shell])
end

def cmd_container(args : Array(String))
  sub    = args.first? || "status"
  engine = detect_engine
  case sub
  when "start"
    puts "  " + cyan("▶") + "  Starting cybersec-mode-env…"
    Process.run(engine, ["start", "cybersec-mode-env"], output: STDOUT, error: STDERR)
  when "stop"
    puts "  " + yellow("■") + "  Stopping cybersec-mode-env…"
    Process.run(engine, ["stop", "cybersec-mode-env"], output: STDOUT, error: STDERR)
  when "rm"
    puts "  " + red("✕") + "  Removing cybersec-mode-env…"
    Process.run(engine, ["rm", "-f", "cybersec-mode-env"], output: STDOUT, error: STDERR)
  when "logs"
    Process.exec(engine, ["logs", "--tail", "100", "-f", "cybersec-mode-env"])
  else
    puts red("  ✗  Unknown: #{sub}  —  start|stop|rm|logs")
  end
end

def cmd_tools(args : Array(String))
  filter = args.first?.try(&.downcase)
  red_cats = {
    "Recon"       => ["nmap","masscan","rustscan","theHarvester","amass","subfinder","recon-ng",
                      "maltego","shodan","dnsenum","dnsrecon","fierce","whois","enum4linux",
                      "netdiscover","smbmap","ldapdomaindump","kerbrute","fping","unicornscan"],
    "Web"         => ["burpsuite","sqlmap","nikto","gobuster","feroxbuster","ffuf","wfuzz",
                      "dirsearch","whatweb","nuclei","dalfox","xsstrike","commix","wpscan",
                      "joomscan","droopescan","wafw00f","arjun","hakrawler","gau","waybackurls"],
    "Exploit"     => ["msfconsole","searchsploit","beef-xss","setoolkit","impacket","responder",
                      "certipy","evil-winrm","crackmapexec","printspoofer","juicypotato","roguepotato",
                      "exploitdb","yersinia","heartbleed"],
    "Passwords"   => ["hashcat","john","hydra","medusa","cewl","crunch","cupp","ophcrack",
                      "patator","spray","kerbrute","ntlmrelayx","hashid","hash-identifier","pypykatz"],
    "Network"     => ["netcat","ncat","tcpdump","wireshark","tshark","scapy","hping3","bettercap",
                      "ettercap","arpspoof","sslstrip","proxychains","tor","mitm6","dnsspoof",
                      "sslscan","testssl","sslyze"],
    "Wireless"    => ["aircrack-ng","airmon-ng","airodump-ng","aireplay-ng","wifite","hostapd-wpe",
                      "bully","pixiewps","wash","reaver","kismet","mdk4","cowpatty"],
    "Forensics"   => ["binwalk","volatility3","ghidra","radare2","gdb","strace","strings","exiftool",
                      "foremost","pwntools","checksec","objdump","ltrace","file","yara","pe-tree"],
    "Post-Exploit"=> ["mimikatz","bloodhound","neo4j","chisel","ligolo-ng","pspy","linpeas",
                      "winpeas","powercat","smbexec","psexec","wmiexec","dcomexec","lsassy",
                      "secretsdump","ticketer"],
  }
  blue_cats = {
    "Monitoring"  => ["wireshark","tshark","tcpdump","zeek","arkime","ntopng","iftop","nethogs",
                      "iptraf-ng","ss","netstat","netflow","darkstat","bandwhich","vnstat","iftop"],
    "IDS/IPS"     => ["suricata","snort","ossec","wazuh","aide","samhain","fail2ban","psad",
                      "tripwire","denyhosts","sshguard","crowdsec","modsecurity","fwknop"],
    "Scanning"    => ["openvas","nessus","nmap","nuclei","lynis","grype","trivy","prowler",
                      "cve-search","vulmap","dockle","kube-bench","checkov","scoutsuite",
                      "nessuscli","greenbone"],
    "Hardening"   => ["auditd","apparmor","selinux","ufw","iptables","nftables","chkrootkit",
                      "rkhunter","tiger","bastille","pass","age","cryptsetup","firejail",
                      "debsums","rpm-verify"],
    "Malware"     => ["clamav","yara","volatility3","ghidra","radare2","cuckoo","binwalk",
                      "strings","exiftool","maldet","loki","fenrir","cape","remnux"],
    "SIEM"        => ["elk","graylog","loki","grafana","splunk","chainsaw","sigma","timesketch",
                      "velociraptor","fluentd","logstash","kibana","opensearch","wazuh-indexer"],
    "Forensics"   => ["autopsy","sleuthkit","foremost","photorec","dd","dc3dd","testdisk",
                      "bulk_extractor","plaso","log2timeline","regripper","volatility3",
                      "fdisk","parted","mount"],
    "Compliance"  => ["openscap","inspec","ansible-hardening","prowler","dockle","kube-bench",
                      "lynis","oscap","vuls","tiger","conftest","terrascan","tfsec","checkov"],
  }
  if filter
    found = red_cats[filter.capitalize]? || blue_cats[filter.capitalize]?
    if found
      puts bold("  Tools: #{filter.capitalize}")
      puts ""
      found.each { |t| puts "    #{cyan("▸")} #{t}" }
    else
      puts red("  ✗  Category '#{filter}' not found.")
    end
    puts ""
    return
  end
  puts bold("  🔴 RED MODE — #{red_cats.values.sum(&.size)} tools")
  red_cats.each { |cat, tools| puts "    #{red(cat.ljust(14))}  #{dim(tools.join(", "))}" }
  puts ""
  puts bold("  🔵 BLUE MODE — #{blue_cats.values.sum(&.size)} tools")
  blue_cats.each { |cat, tools| puts "    #{cyan(cat.ljust(14))}  #{dim(tools.join(", "))}" }
  puts ""
end

def cmd_version
  puts "  #{bold(APP_NAME)} #{cyan("v#{VERSION}")} — #{dim("HackerOS")} — #{dim("Shell: #{HSH_BIN}")}"
end

# ── back mode ─────────────────────────────────────────────────────────────
#
# cybersec back         — switch back to Cybersecurity Mode session (tty3)
# cybersec back kde     — switch back to KDE Plasma session (tty2)
# cybersec back mode    — switch back to Cybersec Mode OR launch it
#
# TTY layout (convention):
#   tty1  — getty / console
#   tty2  — KDE Plasma (startplasma-wayland)
#   tty3  — Cybersecurity Mode (cage cybersec-mode-main)
#
# The button "Switch Back" in the GUI status bar triggers:
#   cybersec back kde

def chvt(n : Int32)
  Process.run("chvt", [n.to_s], error: Process::Redirect::Close)
end

def cybersec_session_running? : Bool
  # Check if cage/cybersec-mode-main is running on any tty
  out = ""
  Process.run("bash", ["-c", "loginctl list-sessions --no-legend 2>/dev/null | grep -c cybersec || echo 0"],
    output: Process::Redirect::Pipe) { |p| out = p.output.gets_to_end.strip }
  out.to_i? != 0
rescue
  false
end

def plasma_session_running? : Bool
  out = ""
  Process.run("bash", ["-c", "loginctl list-sessions --no-legend 2>/dev/null | grep -c plasmashell || echo 0"],
    output: Process::Redirect::Pipe) { |p| out = p.output.gets_to_end.strip }
  out.to_i? != 0
rescue
  false
end

def cmd_back(args : Array(String))
  target = args.first? || "mode"

  case target
  when "kde", "plasma"
    banner
    puts "  #{bold("⇄  Switching to KDE Plasma")}  #{dim("(tty2)")}"
    puts ""
    if plasma_session_running?
      puts "  " + cyan("▶") + "  Plasma running — switching to tty2…"
      chvt(2)
    else
      puts "  " + yellow("⚠") + "  KDE Plasma not running — starting startplasma-wayland on tty2…"
      # Start plasma in background then switch tty
      Process.run("bash", ["-c",
        "nohup startplasma-wayland > /tmp/plasma-start.log 2>&1 &"
      ])
      sleep(2)
      chvt(2)
      puts "  " + green("✓") + "  Switched to tty2."
    end

  when "mode", "cybersec"
    banner
    puts "  #{bold("⇄  Switching to Cybersecurity Mode")}  #{dim("(tty3)")}"
    puts ""
    if cybersec_session_running?
      puts "  " + cyan("▶") + "  Session found — switching to tty3…"
      chvt(3)
    else
      puts "  " + yellow("⚠") + "  No Cybersecurity Mode session found — launching…"
      unless executable?(GUI_BIN)
        puts "  " + red("✗") + "  GUI binary not found: #{GUI_BIN}"
        exit 1
      end
      shell = executable?(HSH_BIN) ? HSH_BIN : "/bin/bash"
      env = {
        "XDG_SESSION_TYPE" => "wayland",
        "CYBERSEC_SESSION" => "1",
        "CYBERSEC_SHELL"   => shell,
      }
      if executable?(CAGE_BIN)
        Process.run("bash", ["-c",
          "nohup #{CAGE_BIN} #{GUI_BIN} > /tmp/cybersec-session.log 2>&1 &"
        ])
      else
        Process.run("bash", ["-c",
          "nohup #{GUI_BIN} > /tmp/cybersec-session.log 2>&1 &"
        ])
      end
      sleep(1)
      chvt(3)
      puts "  " + green("✓") + "  Session launched on tty3."
    end

  else
    puts red("  ✗  Unknown back target: #{target}")
    puts dim("     Use: cybersec back [kde|mode]")
    exit 1
  end
end

# ── Main ───────────────────────────────────────────────────────────────────

args = ARGV.to_a

if args.empty?
  cmd_launch_session
  exit 0
end

subcommand = args[0]
rest       = args[1..]

case subcommand
when "please"                    then cmd_launch_in_session
when "help", "--help", "-h"      then cmd_help
when "update"                    then cmd_update
when "plugin"                    then cmd_plugin(rest)
when "status"                    then cmd_status
when "set-mode"                  then cmd_set_mode(rest)
when "exec"                      then cmd_exec(rest)
when "shell"                     then cmd_shell
when "container"                 then cmd_container(rest)
when "tools"                     then cmd_tools(rest)
when "back"                      then cmd_back(rest)
when "version", "--version", "-v" then cmd_version
else
  puts red("  ✗  Unknown command: #{subcommand}")
  puts dim("     Run 'cybersec help' for usage.")
  exit 1
end
