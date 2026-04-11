require "option_parser"
require "json"
require "process"
require "colorize"

VERSION     = "1.0.0"
APP_NAME    = "Cybersecurity Mode"
GUI_BIN     = "/usr/lib/HackerOS/Cybersecurity-Mode/cybersec-mode-main"
BACKEND_BIN = "/usr/lib/HackerOS/Cybersecurity-Mode/cybersec-mode-backend"
CAGE_BIN    = "/usr/bin/cage"
CACHE_DIR   = "#{Path.home}/.cache/HackerOS/Cybersecurity-Mode"
CONFIG_FILE = "#{CACHE_DIR}/config.json"
PLUGIN_DIR  = "#{CACHE_DIR}/plugins"

# ── Helpers ────────────────────────────────────────────────────────────────

def red(text)    : String;    text.colorize(:red).to_s    end
def green(text)  : String;    text.colorize(:green).to_s  end
def yellow(text) : String;    text.colorize(:yellow).to_s end
def cyan(text)   : String;    text.colorize(:cyan).to_s   end
def bold(text)   : String;    text.colorize.bold.to_s     end
def dim(text)    : String;    text.colorize(:dark_gray).to_s end

def banner
  puts <<-BANNER
#{cyan("╔══════════════════════════════════════════════╗")}
#{cyan("║")}  #{bold("Cybersecurity Mode")}  #{dim("v#{VERSION}")}  #{cyan("│")}  #{bold("HackerOS")}       #{cyan("║")}
#{cyan("╚══════════════════════════════════════════════╝")}
BANNER
end

def config_get(key : String) : String?
  return nil unless File.exists?(CONFIG_FILE)
  JSON.parse(File.read(CONFIG_FILE))[key]?.try(&.as_s?)
rescue
  nil
end

def config_set(key : String, value : String)
  Dir.mkdir_p(CACHE_DIR)
  data = File.exists?(CONFIG_FILE) ? JSON.parse(File.read(CONFIG_FILE)).as_h : {} of String => JSON::Any
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
    puts red("✗  This command requires a TTY session.")
    puts dim("   Run from a terminal, not from within the GUI.")
    exit 1
  end
end

def binary_exists?(path : String) : Bool
  File.executable?(path)
end

# ── Commands ───────────────────────────────────────────────────────────────

def cmd_launch_session
  require_tty!
  unless binary_exists?(GUI_BIN)
    puts red("✗  Cybersecurity Mode binary not found: #{GUI_BIN}")
    puts dim("   Install HackerOS Cybersecurity Mode package.")
    exit 1
  end

  banner
  puts green("▶  Launching Cybersecurity Mode session via cage…")

  if binary_exists?(CAGE_BIN)
    Process.exec(CAGE_BIN, [GUI_BIN], env: {"XDG_SESSION_TYPE" => "wayland", "CYBERSEC_SESSION" => "1"})
  else
    puts yellow("⚠  cage not found — launching without Wayland compositor")
    Process.exec(GUI_BIN, env: {"CYBERSEC_SESSION" => "1"})
  end
end

def cmd_launch_in_session
  unless binary_exists?(GUI_BIN)
    puts red("✗  Binary not found: #{GUI_BIN}")
    exit 1
  end
  puts green("▶  Launching Cybersecurity Mode in current session…")
  Process.exec(GUI_BIN)
end

def cmd_help
  banner
  puts ""
  puts bold("USAGE")
  puts "  #{cyan("cybersec")}               Launch Cybersecurity Mode session (TTY only)"
  puts "  #{cyan("cybersec please")}        Launch GUI in existing session"
  puts "  #{cyan("cybersec help")}          Show this help message"
  puts "  #{cyan("cybersec update")}        Update tools, container image, and app"
  puts "  #{cyan("cybersec plugin")}        Plugin management"
  puts "  #{cyan("cybersec status")}        Show container and system status"
  puts "  #{cyan("cybersec set-mode")} M    Set mode: red | blue"
  puts "  #{cyan("cybersec exec")} CMD      Execute command in container"
  puts "  #{cyan("cybersec version")}       Print version"
  puts ""
  puts bold("PLUGIN SUBCOMMANDS")
  puts "  #{cyan("cybersec plugin list")}            List installed plugins"
  puts "  #{cyan("cybersec plugin install")} NAME     Install a plugin"
  puts "  #{cyan("cybersec plugin remove")} NAME      Remove a plugin"
  puts "  #{cyan("cybersec plugin info")} NAME        Show plugin details"
  puts ""
  puts bold("EXAMPLES")
  puts dim("  # Start a full Cybersecurity Mode TTY session")
  puts "  cybersec"
  puts ""
  puts dim("  # Open GUI inside an existing session (e.g. from terminal emulator)")
  puts "  cybersec please"
  puts ""
  puts dim("  # Run nmap inside the container")
  puts "  cybersec exec 'nmap -sV 192.168.1.0/24'"
  puts ""
  puts dim("  # Switch to blue mode")
  puts "  cybersec set-mode blue"
  puts ""
  puts "  #{dim("Logs:")}"
  puts dim("  ~/.local/share/HackerOS/Cybersecurity-Mode/logs/")
  puts "  #{dim("Cache:")}"
  puts dim("  #{CACHE_DIR}")
end

def cmd_update
  banner
  puts bold("\n⬆  Updating Cybersecurity Mode…\n")
  puts dim("─" * 48)

  steps = [
    {
      "label" => "Checking for app updates",
      "cmd"   => ["echo", "[PLACEHOLDER] App update check — coming soon"],
    },
    {
      "label" => "Pulling latest container image",
      "cmd"   => ["podman", "pull", "blackarchlinux/blackarch"],
    },
    {
      "label" => "Updating BlackArch keyring",
      "cmd"   => ["podman", "exec", "cybersec-mode-env", "bash", "-c",
                  "pacman -Sy --noconfirm blackarch-keyring 2>/dev/null || echo 'Container not running, skipped'"],
    },
    {
      "label" => "Updating container packages",
      "cmd"   => ["podman", "exec", "cybersec-mode-env", "bash", "-c",
                  "pacman -Syu --noconfirm 2>/dev/null || echo 'Container not running, skipped'"],
    },
  ]

  steps.each_with_index do |step, i|
    puts "\n#{cyan("[#{i+1}/#{steps.size}]")} #{step["label"]}"
    cmd = step["cmd"].as(Array(String))
    status = Process.run(cmd[0], cmd[1..], output: STDOUT, error: STDERR)
    if status.success?
      puts green("  ✓ Done")
    else
      puts yellow("  ⚠ Step finished with warnings (exit #{status.exit_code})")
    end
  end

  puts "\n#{green("✓")} Update complete.\n"
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
      puts dim("  No plugins installed.")
      puts dim("  Install with: cybersec plugin install <name>")
    else
      puts bold("Installed plugins:")
      plugins.each { |p| puts "  #{cyan("▸")} #{p}" }
    end

  when "install"
    name = args[1]?
    if name.nil?
      puts red("✗  Usage: cybersec plugin install <name>")
      exit 1
    end
    puts yellow("⚠  Plugin system is not yet implemented.")
    puts dim("   Plugin: #{name}")
    puts dim("   Coming in Cybersecurity Mode v1.1")

  when "remove"
    name = args[1]?
    if name.nil?
      puts red("✗  Usage: cybersec plugin remove <name>")
      exit 1
    end
    plugin_file = "#{PLUGIN_DIR}/#{name}.json"
    if File.exists?(plugin_file)
      File.delete(plugin_file)
      puts green("✓  Plugin '#{name}' removed.")
    else
      puts red("✗  Plugin '#{name}' is not installed.")
    end

  when "info"
    name = args[1]?
    if name.nil?
      puts red("✗  Usage: cybersec plugin info <name>")
      exit 1
    end
    plugin_file = "#{PLUGIN_DIR}/#{name}.json"
    if File.exists?(plugin_file)
      puts File.read(plugin_file)
    else
      puts red("✗  Plugin '#{name}' not found.")
    end

  else
    puts red("✗  Unknown plugin subcommand: #{sub}")
    puts dim("   Use: list | install | remove | info")
  end
end

def cmd_status
  banner
  puts bold("\n📊  System Status\n")

  # Container
  engine = File.executable?("/usr/bin/podman") ? "podman" : "docker"
  puts "  #{bold("Container Engine:")} #{cyan(engine)}"

  status = Process.run(engine, ["inspect", "--format", "{{.State.Status}}", "cybersec-mode-env"],
                        output: Process::Redirect::Pipe, error: Process::Redirect::Close) do |p|
    p.output.gets_to_end.strip
  end
  container_state = status rescue "not found"
  color = container_state == "running" ? :green : :red
  puts "  #{bold("Container:")}        #{container_state.colorize(color)}"

  # Mode
  mode = config_get("mode") || "not set"
  mode_color = mode == "red" ? :red : :blue
  puts "  #{bold("Mode:")}             #{mode.colorize(mode_color)}"

  # App binary
  gui_ok = File.executable?(GUI_BIN)
  puts "  #{bold("GUI Binary:")}       #{(gui_ok ? "✓ found" : "✗ missing").colorize(gui_ok ? :green : :red)}"
  be_ok = File.executable?(BACKEND_BIN)
  puts "  #{bold("Backend Binary:")}   #{(be_ok ? "✓ found" : "✗ missing").colorize(be_ok ? :green : :red)}"

  # Config
  cfg_ok = File.exists?(CONFIG_FILE)
  puts "  #{bold("Config:")}           #{cfg_ok ? cyan(CONFIG_FILE) : dim("not found")}"

  puts ""
end

def cmd_set_mode(args : Array(String))
  mode = args.first?
  unless mode == "red" || mode == "blue"
    puts red("✗  Invalid mode. Use: red | blue")
    exit 1
  end
  config_set("mode", mode)
  color = mode == "red" ? :red : :blue
  puts "#{green("✓")} Mode set to #{mode.colorize(color)}."
end

def cmd_exec(args : Array(String))
  cmd_str = args.join(" ")
  if cmd_str.empty?
    puts red("✗  Usage: cybersec exec <command>")
    exit 1
  end
  engine = File.executable?("/usr/bin/podman") ? "podman" : "docker"
  Process.exec(engine, ["exec", "-it", "cybersec-mode-env", "bash", "-c", cmd_str])
end

def cmd_version
  puts "#{bold(APP_NAME)} #{cyan("v#{VERSION}")} — #{dim("HackerOS")}"
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
when "please"
  cmd_launch_in_session
when "help", "--help", "-h"
  cmd_help
when "update"
  cmd_update
when "plugin"
  cmd_plugin(rest)
when "status"
  cmd_status
when "set-mode"
  cmd_set_mode(rest)
when "exec"
  cmd_exec(rest)
when "version", "--version", "-v"
  cmd_version
else
  puts red("✗  Unknown command: #{subcommand}")
  puts dim("   Run 'cybersec help' for usage.")
  exit 1
end
