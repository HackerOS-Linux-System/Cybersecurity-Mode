// src/rpc/mod.rs — JSON-RPC over Unix socket
use anyhow::Result;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::UnixStream;
use tracing::{debug, warn};

use crate::container;

#[derive(Deserialize, Debug)]
struct Request {
    method: String,
    #[serde(default)]
    params: Value,
}

#[derive(Serialize)]
struct Response {
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

impl Response {
    fn ok(result: Value) -> Self {
        Self { ok: true, result: Some(result), error: None }
    }
    fn err(msg: impl Into<String>) -> Self {
        Self { ok: false, result: None, error: Some(msg.into()) }
    }
}

pub async fn handle_connection(stream: UnixStream) -> Result<()> {
    let (reader, mut writer) = stream.into_split();
    let mut lines = BufReader::new(reader).lines();

    while let Some(line) = lines.next_line().await? {
        let line = line.trim().to_string();
        if line.is_empty() { continue; }

        debug!("RPC request: {line}");

        let response = match serde_json::from_str::<Request>(&line) {
            Ok(req) => dispatch(req).await,
            Err(e)  => Response::err(format!("Parse error: {e}")),
        };

        let mut out = serde_json::to_string(&response)?;
        out.push('\n');
        writer.write_all(out.as_bytes()).await?;
    }
    Ok(())
}

async fn dispatch(req: Request) -> Response {
    match req.method.as_str() {
        "ping" => Response::ok(json!({"pong": true})),

        "container_status" => {
            let name = req.params["name"].as_str().unwrap_or("cybersec-mode-env");
            match container::status(name).await {
                Ok(s)  => Response::ok(s),
                Err(e) => Response::err(e.to_string()),
            }
        }

        "container_start" => {
            let image = req.params["image"].as_str().unwrap_or("blackarchlinux/blackarch");
            let name  = req.params["name"].as_str().unwrap_or("cybersec-mode-env");
            match container::start(image, name).await {
                Ok(s)  => Response::ok(s),
                Err(e) => Response::err(e.to_string()),
            }
        }

        "container_stop" => {
            let name = req.params["name"].as_str().unwrap_or("cybersec-mode-env");
            match container::stop(name).await {
                Ok(s)  => Response::ok(s),
                Err(e) => Response::err(e.to_string()),
            }
        }

        "container_exec" => {
            let name = req.params["name"].as_str().unwrap_or("cybersec-mode-env");
            let cmd  = req.params["cmd"].as_str().unwrap_or("");
            match container::exec(name, cmd).await {
                Ok(s)  => Response::ok(s),
                Err(e) => Response::err(e.to_string()),
            }
        }

        "list_tools" => {
            Response::ok(json!({
                "tools": [
                    "nmap","metasploit","burpsuite","sqlmap","hydra",
                    "aircrack-ng","hashcat","john","gobuster","nikto",
                    "wireshark","netcat","suricata","lynis","openvas",
                    "fail2ban","auditd","clamav","rkhunter","tcpdump"
                ]
            }))
        }

        "system_info" => Response::ok(system_info().await),

        "scan_network" => {
            let target = req.params["target"].as_str().unwrap_or("");
            match scan_network(target).await {
                Ok(s)  => Response::ok(s),
                Err(e) => Response::err(e.to_string()),
            }
        }

        unknown => {
            warn!("Unknown method: {unknown}");
            Response::err(format!("Unknown method: {unknown}"))
        }
    }
}

async fn system_info() -> Value {
    use std::process::Command;

    let hostname = Command::new("hostname")
    .output()
    .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
    .unwrap_or_else(|_| "unknown".into());

    let kernel = Command::new("uname")
    .arg("-r")
    .output()
    .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
    .unwrap_or_else(|_| "unknown".into());

    let uptime = Command::new("uptime")
    .arg("-p")
    .output()
    .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
    .unwrap_or_else(|_| "unknown".into());

    json!({
        "hostname": hostname,
        "kernel":   kernel,
        "uptime":   uptime,
        "os":       "HackerOS",
    })
}

async fn scan_network(target: &str) -> Result<Value> {
    use tokio::process::Command;
    let output = Command::new("nmap")
    .args(["-sn", target, "--open", "-oX", "-"])
    .output()
    .await?;
    Ok(json!({
        "target": target,
        "raw":    String::from_utf8_lossy(&output.stdout),
             "exit_code": output.status.code(),
    }))
}
