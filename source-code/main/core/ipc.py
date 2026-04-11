from __future__ import annotations
import json
import logging
import os
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional


SOCK_PATH = "/tmp/cybersec-mode-backend.sock"
TIMEOUT   = 5.0


class IPCClient:
    """
    Manages connection to the cybersec-mode-backend Rust process.
    Sends JSON requests, receives JSON responses over Unix domain socket.
    """

    def __init__(self, backend_bin: Path, sock_path: str = SOCK_PATH):
        self._bin       = backend_bin
        self._sock_path = sock_path
        self._proc: Optional[subprocess.Popen] = None
        self._sock: Optional[socket.socket]    = None
        self._lock      = threading.Lock()
        self._logger    = logging.getLogger("IPC")

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self):
        """Launch backend process and connect to its socket."""
        if not self._bin.exists():
            self._logger.warning("Backend binary not found, IPC disabled")
            return
        try:
            if os.path.exists(self._sock_path):
                os.unlink(self._sock_path)
            self._proc = subprocess.Popen(
                [str(self._bin), "--socket", self._sock_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for socket to appear
            for _ in range(50):
                if os.path.exists(self._sock_path):
                    break
                time.sleep(0.1)
            self._connect()
        except Exception as e:
            self._logger.error(f"Failed to start backend: {e}")

    def stop(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def _connect(self):
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.settimeout(TIMEOUT)
            self._sock.connect(self._sock_path)
            self._logger.info("Connected to backend socket")
        except Exception as e:
            self._logger.error(f"Socket connect failed: {e}")
            self._sock = None

    # ── RPC ───────────────────────────────────────────────────────────────

    def call(self, method: str, params: dict = None) -> Optional[dict]:
        """Synchronous JSON-RPC call to backend."""
        if not self._sock:
            return None
        req = json.dumps({"method": method, "params": params or {}}) + "\n"
        with self._lock:
            try:
                self._sock.sendall(req.encode())
                buf = b""
                while b"\n" not in buf:
                    chunk = self._sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                return json.loads(buf.strip())
            except Exception as e:
                self._logger.error(f"IPC call failed: {e}")
                return None

    def call_async(self, method: str, params: dict,
                   callback: Callable[[Optional[dict]], None]):
        """Non-blocking call, result delivered to callback on a thread."""
        def _run():
            result = self.call(method, params)
            callback(result)
        threading.Thread(target=_run, daemon=True).start()

    # ── Convenience wrappers ──────────────────────────────────────────────

    def get_container_status(self) -> dict:
        result = self.call("container_status")
        return result or {"running": False, "error": "backend unavailable"}

    def start_container(self, image: str, name: str) -> dict:
        return self.call("container_start", {"image": image, "name": name}) or {}

    def stop_container(self, name: str) -> dict:
        return self.call("container_stop", {"name": name}) or {}

    def exec_in_container(self, name: str, cmd: str) -> dict:
        return self.call("container_exec", {"name": name, "cmd": cmd}) or {}

    def list_tools(self) -> list:
        result = self.call("list_tools")
        return result.get("tools", []) if result else []

    def scan_network(self, target: str, options: dict) -> dict:
        return self.call("scan_network", {"target": target, **options}) or {}

    def get_system_info(self) -> dict:
        return self.call("system_info") or {}
