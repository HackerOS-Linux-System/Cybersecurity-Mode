from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "mode": None,               # "red" | "blue" — None means not yet chosen
    "always_ask_mode": True,
    "theme": "dark_gray",       # dark_gray | dark_black | dark_slate | light
    "font_size": 13,
    "terminal_font": "JetBrains Mono",
    "terminal_font_size": 13,
    "shell": "bash",
    "container_engine": "podman",
    "container_image": "blackarchlinux/blackarch",
    "container_name": "cybersec-mode-env",
    "backend_socket": "/tmp/cybersec-mode-backend.sock",
    "session_mode": False,       # running as dedicated TTY session?
    "show_welcome": True,
    "sidebar_collapsed": False,
    "log_level": "INFO",
    "keybindings": {
        "toggle_terminal": "Ctrl+T",
        "toggle_docs":     "Ctrl+D",
        "toggle_main":     "Ctrl+M",
        "toggle_settings": "Ctrl+,",
        "hacker_menu":     "Ctrl+H",
    },
}


class ConfigManager:
    """Thread-safe JSON config with dot-path access."""

    def __init__(self, path: Path):
        self._path  = path
        self._lock  = threading.Lock()
        self._data: dict[str, Any] = {}
        self._load()

    # ── I/O ───────────────────────────────────────────────────────────────

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # Merge stored over defaults
                self._data = {**DEFAULT_CONFIG, **stored}
                return
            except (json.JSONDecodeError, OSError):
                pass
        self._data = dict(DEFAULT_CONFIG)

    def save(self):
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)

    # ── Access ────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._data)

    def update(self, updates: dict):
        with self._lock:
            self._data.update(updates)
