mod hk_parser;
mod apps;
mod cli;
mod compositor_bridge;
mod config;
mod container;
mod environment;
mod ipc;
mod mode;
mod please;
mod theme;
mod tools;

// Single slint::include_modules!() for entire crate — generates all Slint types
slint::include_modules!();

use anyhow::Result;
use clap::{Parser, Subcommand};
use colored::Colorize;

const VERSION: &str = "0.2.0";
const BANNER: &str = r#"
  ██████╗███╗   ███╗
 ██╔════╝████╗ ████║   CM — Cybersecurity Mode v0.2
 ██║     ██╔████╔██║   HackerOS Red Team Edition
 ██║     ██║╚██╔╝██║   ─────────────────────────
 ╚██████╗██║ ╚═╝ ██║   Rust · Slint · Smithay
  ╚═════╝╚═╝     ╚═╝
"#;

#[derive(Parser, Debug)]
#[command(name = "cm", version = VERSION, about = "HackerOS Cybersecurity Mode")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Launch CM as floating app in current session
    Please,
    /// Switch TTY and launch CM
    Back {
        #[command(subcommand)]
        target: BackTarget,
    },
    /// Launch CM Environment (full DE, needs TTY or nested Wayland)
    Environment,
    /// Launch CM Mode — Red Team suite (needs TTY)
    Mode,
    /// Launch a CM Environment application
    App {
        #[arg(value_name = "APP")]
        name: String,
        #[arg(trailing_var_arg = true)]
        args: Vec<String>,
    },
    /// Show system & container status
    Status,
    /// Show version
    Version,
    /// Internal: run compositor subprocess
    #[command(name = "__compositor__", hide = true)]
    Compositor { mode: String },
}

#[derive(Subcommand, Debug)]
enum BackTarget {
    /// Switch to tty3 → CM Mode
    Mode,
    /// Switch to tty2 → CM Environment
    Environment,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .compact()
        .init();

    let cli = Cli::parse();

    match cli.command {
        None => print_help(),

        Some(Commands::Please) => {
            println!("{}", BANNER.bright_red());
            please::run().await?;
        }

        Some(Commands::Back { target }) => match target {
            BackTarget::Mode => {
                println!("{}", "  → tty3 CM Mode".red());
                cli::switch_tty(3, "mode").await?;
            }
            BackTarget::Environment => {
                println!("{}", "  → tty2 CM Environment".cyan());
                cli::switch_tty(2, "environment").await?;
            }
        },

        Some(Commands::Environment) => {
            println!("{}", BANNER.bright_cyan());
            environment::run().await?;
        }

        Some(Commands::Mode) => {
            println!("{}", BANNER.bright_red());
            mode::run().await?;
        }

        Some(Commands::App { name, args }) => {
            apps::launch(&name, &args).await?;
        }

        Some(Commands::Status) => {
            cli::print_status().await?;
        }

        Some(Commands::Version) => {
            println!("{}", BANNER.bright_red());
            println!("  {} {}", "cm".bright_white().bold(), VERSION.bright_green());
            println!("  HackerOS Cybersecurity Mode — Red Team Edition");
            println!("  Rust + Slint + Smithay + XWayland + hk-parser");
        }

        Some(Commands::Compositor { mode }) => {
            let cm = if mode == "mode" {
                compositor_bridge::CompositorMode::Mode
            } else {
                compositor_bridge::CompositorMode::Environment
            };
            compositor_bridge::run_compositor(cm)?;
        }
    }

    Ok(())
}

fn print_help() {
    println!("{}", BANNER.bright_red());
    println!("{}", "COMMANDS".bright_white().bold());
    println!();
    let cmds = [
        ("cm please",           "Floating app — uses current Wayland/X session"),
        ("cm back mode",        "Switch to tty3 → CM Mode Red Team session"),
        ("cm back environment", "Switch to tty2 → CM Environment full DE"),
        ("cm environment",      "Full desktop environment with own compositor"),
        ("cm mode",             "Red Team tool suite with own compositor"),
        ("cm app <name>",       "Launch CM app"),
        ("cm status",           "System & container status"),
        ("cm version",          "Version info"),
        ("cm --help",           "Full help"),
    ];
    for (cmd, desc) in &cmds {
        println!("  {:<32} {}", cmd.bright_green(), desc.white());
    }
    println!();
    println!("{}", "CM APPS (cm app <name>)".bright_white().bold());
    println!();
    for app in &["settings","about","emoji-picker","calculator","containers","clipboard"] {
        println!("  {}", format!("cm app {}", app).bright_cyan());
    }
    println!();
    println!("{}", "CM ENVIRONMENT — default apps".bright_white().bold());
    println!();
    let defaults = [
        ("Terminal",        "Hacker Term (external)"),
        ("File Manager",    "nemo"),
        ("Text Editor",     "kate"),
        ("Browser",         "mullvad-browser"),
        ("System Monitor",  "stacer"),
        ("Clipboard",       "CM own (cm app clipboard)"),
        ("Screenshots",     "spectacle"),
        ("Documents",       "papers"),
        ("Image Viewer",    "loupe"),
        ("Media Player",    "haruna"),
        ("Email",           "thunderbird"),
    ];
    for (role, app) in &defaults {
        println!("  {:<20} {}", role.bright_white(), app.white());
    }
    println!();
}
