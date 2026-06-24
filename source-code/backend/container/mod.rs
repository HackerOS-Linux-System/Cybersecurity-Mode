// src/container/mod.rs — Podman/Docker container lifecycle management
use anyhow::{Context, Result};
use serde_json::{json, Value};
use tokio::process::Command;
use tracing::{debug, info};

fn engine() -> &'static str {
    // Prefer podman; fall back to docker
    if std::path::Path::new("/usr/bin/podman").exists()
        || std::path::Path::new("/usr/local/bin/podman").exists()
        {
            "podman"
        } else {
            "docker"
        }
}

/// Check if a named container is running.
pub async fn status(name: &str) -> Result<Value> {
    let out = Command::new(engine())
    .args(["inspect", "--format", "{{.State.Status}}", name])
    .output()
    .await
    .context("Failed to run container engine")?;

    let state = String::from_utf8_lossy(&out.stdout).trim().to_string();
    let running = state == "running";

    debug!("Container '{name}' status: {state}");
    Ok(json!({
        "name":    name,
        "running": running,
        "state":   state,
        "engine":  engine(),
    }))
}

/// Start or create the container.
pub async fn start(image: &str, name: &str) -> Result<Value> {
    // Try to start existing container first
    let start_out = Command::new(engine())
    .args(["start", name])
    .output()
    .await?;

    if start_out.status.success() {
        info!("Started existing container: {name}");
        return Ok(json!({"started": true, "name": name, "reused": true}));
    }

    // Create and start new container
    info!("Creating container '{name}' from image '{image}'");
    let out = Command::new(engine())
    .args([
        "run", "-d",
        "--name", name,
        "--privileged",
        "--network", "host",
        "--security-opt", "seccomp=unconfined",
        "--cap-add", "NET_ADMIN",
        "--cap-add", "NET_RAW",
        "-v", "/home:/home:rw",
        "-v", "/tmp/cybersec:/tmp/cybersec:rw",
        image,
        "sleep", "infinity",
    ])
    .output()
    .await
    .context("Failed to create container")?;

    let success = out.status.success();
    let stderr  = String::from_utf8_lossy(&out.stderr).trim().to_string();

    if !success {
        return Err(anyhow::anyhow!("Container start failed: {stderr}"));
    }

    Ok(json!({
        "started": true,
        "name":    name,
        "image":   image,
        "reused":  false,
    }))
}

/// Stop a running container.
pub async fn stop(name: &str) -> Result<Value> {
    info!("Stopping container: {name}");
    let out = Command::new(engine())
    .args(["stop", name])
    .output()
    .await
    .context("Failed to stop container")?;

    Ok(json!({
        "stopped": out.status.success(),
             "name":    name,
    }))
}

/// Execute a command inside the container.
pub async fn exec(name: &str, cmd: &str) -> Result<Value> {
    if cmd.is_empty() {
        return Err(anyhow::anyhow!("Empty command"));
    }

    let out = Command::new(engine())
    .args(["exec", name, "bash", "-c", cmd])
    .output()
    .await
    .context("Failed to exec in container")?;

    Ok(json!({
        "cmd":       cmd,
        "stdout":    String::from_utf8_lossy(&out.stdout),
             "stderr":    String::from_utf8_lossy(&out.stderr),
             "exit_code": out.status.code(),
    }))
}

/// Pull an image.
pub async fn pull(image: &str) -> Result<Value> {
    info!("Pulling image: {image}");
    let out = Command::new(engine())
    .args(["pull", image])
    .output()
    .await
    .context("Failed to pull image")?;

    Ok(json!({
        "image":   image,
        "success": out.status.success(),
             "output":  String::from_utf8_lossy(&out.stdout),
    }))
}

/// List all cybersec containers.
pub async fn list() -> Result<Value> {
    let out = Command::new(engine())
    .args([
        "ps", "-a",
        "--filter", "name=cybersec",
        "--format", "json",
    ])
    .output()
    .await?;

    Ok(json!({
        "containers": String::from_utf8_lossy(&out.stdout),
    }))
}
