# Cybersecurity Mode — HackerOS

Professional security workstation environment for HackerOS.
Offensive penetration testing and defensive auditing in one unified interface.

## Components

| Component | Language | Binary | Path |
|-----------|----------|--------|------|
| GUI Frontend | Python 3.13 + PyQt6 (Nuitka) | `cybersec-mode-main` | `/usr/lib/HackerOS/Cybersecurity-Mode/` |
| Backend | Rust (tokio) | `cybersec-mode-backend` | `/usr/lib/HackerOS/Cybersecurity-Mode/` |
| CLI | Crystal | `cybersec` | `/usr/bin/` |

## Modes

- **🔴 Red Mode** — Offensive / Penetration Testing
- **🔵 Blue Mode** — Defensive / Audit

## Documentation

See `docs/documentation.html` for full documentation.

## Build Requirements

- Python 3.13 + Nuitka + PyQt6
- Rust (cargo ≥ 1.75)
- Crystal (≥ 1.10)
- podman
- cage (for session mode)

## License

HackerOS Project
