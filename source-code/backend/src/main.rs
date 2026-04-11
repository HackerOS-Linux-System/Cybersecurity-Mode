mod container;
mod rpc;

use anyhow::Result;
use clap::Parser;
use std::path::PathBuf;
use tokio::net::UnixListener;
use tracing::{info, error};
use tracing_subscriber::EnvFilter;

#[derive(Parser, Debug)]
#[command(name = "cybersec-mode-backend")]
#[command(about = "HackerOS Cybersecurity Mode backend process")]
struct Args {
    /// Unix socket path for IPC
    #[arg(long, default_value = "/tmp/cybersec-mode-backend.sock")]
    socket: PathBuf,

    /// Log level (TRACE, DEBUG, INFO, WARN, ERROR)
    #[arg(long, default_value = "INFO")]
    log_level: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // Init tracing
    tracing_subscriber::fmt()
    .with_env_filter(
        EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(&args.log_level))
    )
    .init();

    info!("cybersec-mode-backend starting — socket: {:?}", args.socket);

    // Remove stale socket
    if args.socket.exists() {
        std::fs::remove_file(&args.socket)?;
    }

    let listener = UnixListener::bind(&args.socket)?;
    info!("Listening on {:?}", args.socket);

    // Graceful shutdown on SIGTERM / SIGINT
    let socket_path = args.socket.clone();
    tokio::spawn(async move {
        tokio::signal::ctrl_c().await.ok();
        info!("Shutdown signal received");
        let _ = std::fs::remove_file(&socket_path);
        std::process::exit(0);
    });

    loop {
        match listener.accept().await {
            Ok((stream, _)) => {
                tokio::spawn(async move {
                    if let Err(e) = rpc::handle_connection(stream).await {
                        error!("Connection error: {e}");
                    }
                });
            }
            Err(e) => {
                error!("Accept error: {e}");
            }
        }
    }
}
