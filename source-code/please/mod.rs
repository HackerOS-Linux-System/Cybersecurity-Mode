use anyhow::Result;
use slint::{ModelRc, SharedString, VecModel};
use tracing::info;

use crate::container::{self, ContainerStatus};
use crate::tools::RED_TEAM_TOOLS;


pub async fn run() -> Result<()> {
    info!("CM Please starting");
    crate::config::ensure_dirs()?;
    crate::config::init_config_if_missing()?;
    let config = crate::config::CmConfig::load()?;

    let has_wayland = std::env::var("WAYLAND_DISPLAY").is_ok();
    let has_x       = std::env::var("DISPLAY").is_ok();
    if !has_wayland && !has_x {
        return Err(anyhow::anyhow!(
            "No display found. Use 'cm mode' or 'cm environment' from a TTY."
        ));
    }

    std::env::set_var("CM_SESSION_MODE", "please");

    tokio::spawn(async { crate::ipc::serve().await.ok(); });

    run_ui(config).await
}

async fn run_ui(config: crate::config::CmConfig) -> Result<()> {
    let container_name = config.red_team_container.clone();
    let running = container::status(&container_name).await
        .map(|c| c.status == ContainerStatus::Running)
        .unwrap_or(false);

    // Build PleaseToolData — fields match ui/please/main.slint struct PleaseToolData
    let all_tools: Vec<PleaseToolData> = RED_TEAM_TOOLS.iter().map(|t| PleaseToolData {
        name:         t.name.into(),
        display_name: t.display_name.into(),
        description:  t.description.into(),
        icon:         t.icon.into(),
        category:     format!("{:?}", t.category).into(),
        color:        hex_color(t.color),
        difficulty:   format!("{:?}", t.difficulty).into(),
        installed:    which::which(t.command).is_ok(),
        command:      t.command.into(),
    }).collect();

    let tool_model: ModelRc<PleaseToolData> = ModelRc::new(VecModel::from(all_tools.clone()));

    let window = PleaseMainWindow::new()?;
    window.set_tools(tool_model);
    window.set_container_running(running);
    window.set_selected_tab(0);
    window.set_categories(ModelRc::new(VecModel::from(vec![
        SharedString::from("All"),
        "Reconnaissance".into(),
        "WebApplication".into(),
        "Exploitation".into(),
        "PasswordAttacks".into(),
        "Network".into(),
        "Wireless".into(),
        "Forensics".into(),
        "PostExploitation".into(),
        "Evasion".into(),
    ])));

    let terminal_buf = std::sync::Arc::new(std::sync::Mutex::new(String::new()));

    // Container toggle
    {
        let name = container_name.clone();
        let img  = config.container_image.clone();
        let w    = window.as_weak();
        window.on_container_toggle(move || {
            let name = name.clone(); let img = img.clone(); let w = w.clone();
            tokio::spawn(async move {
                let r = container::status(&name).await
                    .map(|c| c.status == ContainerStatus::Running)
                    .unwrap_or(false);
                if r { container::stop(&name).await.ok(); }
                else { container::start(&img, &name).await.ok(); }
                let now = container::status(&name).await
                    .map(|c| c.status == ContainerStatus::Running)
                    .unwrap_or(false);
                w.upgrade_in_event_loop(move |win| win.set_container_running(now)).ok();
            });
        });
    }

    // Tool run
    {
        let name = container_name.clone();
        let buf  = terminal_buf.clone();
        let w    = window.as_weak();
        window.on_tool_run(move |cmd: SharedString| {
            let name = name.clone();
            let cmd  = cmd.to_string();
            let buf  = buf.clone();
            let w    = w.clone();
            tokio::spawn(async move {
                let running = container::status(&name).await
                    .map(|c| c.status == ContainerStatus::Running)
                    .unwrap_or(false);
                if !running {
                    container::start("blackarchlinux/blackarch", &name).await.ok();
                    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                }
                let result = container::exec(&name, &cmd).await;
                let output = match &result {
                    Ok(v)  => format!("$ {}\n{}\n",
                        cmd, v["stdout"].as_str().unwrap_or("")),
                    Err(e) => format!("$ {}\nError: {}\n", cmd, e),
                };
                let mut b = buf.lock().unwrap();
                b.push_str(&output);
                let full = b.clone();
                drop(b);
                w.upgrade_in_event_loop(move |win| {
                    win.set_terminal_output(full.into());
                }).ok();
            });
        });
    }

    // Tool install
    {
        let name = container_name.clone();
        window.on_tool_install(move |tool_name: SharedString| {
            let name = name.clone();
            let tn   = tool_name.to_string();
            let pkg  = RED_TEAM_TOOLS.iter()
                .find(|t| t.name == tn)
                .map(|t| t.package.to_string())
                .unwrap_or_else(|| tn.clone());
            tokio::spawn(async move {
                let running = container::status(&name).await
                    .map(|c| c.status == ContainerStatus::Running)
                    .unwrap_or(false);
                if !running {
                    container::start("blackarchlinux/blackarch", &name).await.ok();
                    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                }
                let script = format!(
                    "pacman -Sy --noconfirm 2>/dev/null; \
                     pacman -S --noconfirm --needed {} 2>&1",
                    pkg
                );
                container::exec(&name, &script).await.ok();
                info!("Installed {} (package: {})", tn, pkg);
            });
        });
    }

    // Terminal submit
    {
        let name = container_name.clone();
        let buf  = terminal_buf.clone();
        let w    = window.as_weak();
        window.on_terminal_submit(move |cmd: SharedString| {
            let name = name.clone();
            let cmd  = cmd.to_string();
            let buf  = buf.clone();
            let w    = w.clone();
            tokio::spawn(async move {
                let out = container::exec(&name, &cmd).await
                    .map(|v| {
                        let stdout = v["stdout"].as_str().unwrap_or("").to_string();
                        let stderr = v["stderr"].as_str().unwrap_or("").to_string();
                        format!("{}{}", stdout, stderr)
                    })
                    .unwrap_or_else(|e| format!("Error: {}", e));
                let mut b = buf.lock().unwrap();
                b.push_str(&format!("❯ {}\n{}\n", cmd, out));
                let full = b.clone();
                drop(b);
                w.upgrade_in_event_loop(move |win| {
                    win.set_terminal_output(full.into());
                }).ok();
            });
        });
    }

    // Search
    {
        let all = all_tools.clone();
        let w   = window.as_weak();
        window.on_search_changed(move |q: SharedString| {
            let q = q.to_string().to_lowercase();
            let filtered: Vec<PleaseToolData> = all.iter()
                .filter(|t| {
                    q.is_empty()
                        || t.name.to_string().to_lowercase().contains(&q)
                        || t.display_name.to_string().to_lowercase().contains(&q)
                        || t.description.to_string().to_lowercase().contains(&q)
                        || t.category.to_string().to_lowercase().contains(&q)
                })
                .cloned().collect();
            let m: ModelRc<PleaseToolData> = ModelRc::new(VecModel::from(filtered));
            w.upgrade_in_event_loop(move |win| win.set_tools(m)).ok();
        });
    }

    // Category filter
    {
        let all = all_tools.clone();
        let w   = window.as_weak();
        window.on_category_changed(move |cat: SharedString| {
            let cat = cat.to_string();
            let filtered: Vec<PleaseToolData> = all.iter()
                .filter(|t| cat == "All" || t.category.to_string() == cat)
                .cloned().collect();
            let m: ModelRc<PleaseToolData> = ModelRc::new(VecModel::from(filtered));
            w.upgrade_in_event_loop(move |win| win.set_tools(m)).ok();
        });
    }

    // Tab change
    {
        let w = window.as_weak();
        window.on_tab_changed(move |i: i32| {
            w.upgrade_in_event_loop(move |win| win.set_selected_tab(i)).ok();
        });
    }

    // Tool clicked
    {
        let w = window.as_weak();
        window.on_tool_clicked(move |i: i32| {
            w.upgrade_in_event_loop(move |win| win.set_selected_tool(i)).ok();
        });
    }

    // Tool launch in terminal (on double-click / run button)
    {
        window.on_tool_launch(move |name: slint::SharedString| {
            let cmd = name.to_string();
            tokio::spawn(async move {
                // Find tool in catalog
                let tool = crate::tools::RED_TEAM_TOOLS.iter()
                    .find(|t| t.name == cmd || t.command == cmd);
                let exec = tool.map(|t| t.command).unwrap_or(cmd.as_str());
                let is_gui = tool.map(|t| t.is_gui).unwrap_or(false);

                if is_gui {
                    tokio::process::Command::new(exec).spawn().ok();
                } else {
                    tokio::process::Command::new(
                        "/usr/share/HackerOS/Scripts/HackerOS-Apps/Hacker-Term"
                    ).args(["-e", exec]).spawn().ok();
                }

                // Notify compositor to bring terminal to front
                tokio::time::sleep(tokio::time::Duration::from_millis(400)).await;
                crate::ipc::send_compositor_command(
                    crate::ipc::CompositorCmd::RaiseWindow { id: 0 }
                ).await.ok();
            });
        });
    }

    window.run()?;
    Ok(())
}

fn hex_color(hex: &str) -> slint::Color {
    let h = hex.trim_start_matches('#');
    if h.len() == 6 {
        if let Ok(n) = u32::from_str_radix(h, 16) {
            return slint::Color::from_rgb_u8(
                ((n >> 16) & 0xff) as u8,
                ((n >>  8) & 0xff) as u8,
                ( n        & 0xff) as u8,
            );
        }
    }
    slint::Color::from_rgb_u8(0xef, 0x44, 0x44)
}
