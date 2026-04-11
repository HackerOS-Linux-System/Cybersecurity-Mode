import logging
import logging.handlers
from pathlib import Path


def setup_logger(log_dir: Path, level: str = "INFO") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "cybersec-mode.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root = logging.getLogger()
    root.setLevel(getattr(logging, level, logging.INFO))

    # Rotating file handler (10 MB × 5 backups)
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler (for TTY sessions)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    return logging.getLogger("CybersecMode")
