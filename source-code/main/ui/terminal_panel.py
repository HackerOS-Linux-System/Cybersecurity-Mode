from __future__ import annotations
import os
import pty
import select
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QLineEdit, QFrame, QSplitter, QSizePolicy,
    QComboBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QProcess
)
from PyQt6.QtGui import QFont, QTextCursor, QColor, QKeyEvent


TERM_STYLE = """
QPlainTextEdit {
    background-color: #0a0a0a;
    color: #00e87a;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px;
    border: none;
    padding: 8px;
    selection-background-color: #1a4a2a;
}
"""

INPUT_STYLE = """
QLineEdit {
    background-color: #0a0a0a;
    color: #00e87a;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px;
    border: none;
    border-top: 1px solid #1e1e1e;
    padding: 6px 10px;
}
"""

HEADER_STYLE = """
QFrame {
    background-color: #111;
    border-bottom: 1px solid #1e1e1e;
}
"""


class ShellProcess(QThread):
    """Runs a subprocess and emits its stdout line by line."""
    output = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, cmd: list[str], env: dict = None):
        super().__init__()
        self._cmd = cmd
        self._env = env
        self._proc = None

    def run(self):
        import subprocess
        env = os.environ.copy()
        if self._env:
            env.update(self._env)
        try:
            self._proc = subprocess.Popen(
                self._cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
            )
            for line in iter(self._proc.stdout.readline, ""):
                self.output.emit(line.rstrip("\n"))
            self._proc.wait()
            self.finished.emit(self._proc.returncode)
        except Exception as e:
            self.output.emit(f"[ERROR] {e}")
            self.finished.emit(1)

    def write(self, data: str):
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(data + "\n")
                self._proc.stdin.flush()
            except Exception:
                pass

    def terminate(self):
        if self._proc:
            self._proc.terminate()


class TerminalWidget(QWidget):
    """Single terminal instance."""

    def __init__(self, title: str, config):
        super().__init__()
        self._config  = config
        self._title   = title
        self._history: list[str] = []
        self._hist_idx = -1
        self._shell   = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        hdr = QFrame()
        hdr.setFixedHeight(32)
        hdr.setStyleSheet(HEADER_STYLE)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(10, 0, 10, 0)

        lbl = QLabel(f"● {title}")
        lbl.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: 700; font-family: monospace;")
        hdr_l.addWidget(lbl)
        hdr_l.addStretch()

        btn_clear = QPushButton("Clear")
        btn_clear.setFixedHeight(22)
        btn_clear.setStyleSheet(
            "background: #1e1e1e; border: 1px solid #2e2e2e; "
            "color: #666; font-size: 10px; border-radius: 3px; padding: 0 8px;"
        )
        btn_clear.clicked.connect(self._clear)
        hdr_l.addWidget(btn_clear)

        layout.addWidget(hdr)

        # Output display
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(TERM_STYLE)
        self.output.setMaximumBlockCount(10_000)
        layout.addWidget(self.output)

        # Input line
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(0)

        prompt = QLabel(" $ ")
        prompt.setStyleSheet(
            "color: #22c55e; font-family: 'JetBrains Mono', monospace; "
            "font-size: 13px; background: #0a0a0a; padding: 6px 0 6px 10px;"
        )
        input_row.addWidget(prompt)

        self.input_line = QLineEdit()
        self.input_line.setStyleSheet(INPUT_STYLE)
        self.input_line.returnPressed.connect(self._submit)
        self.input_line.installEventFilter(self)
        input_row.addWidget(self.input_line)

        layout.addLayout(input_row)

        self._print_banner()
        self._start_shell()

    def _print_banner(self):
        mode  = self._config.get("mode", "red")
        color = "🔴" if mode == "red" else "🔵"
        self._append(
            f"╔══════════════════════════════════════════╗\n"
            f"║   Cybersecurity Mode Terminal  {color}         ║\n"
            f"║   HackerOS  |  Container: blackarch      ║\n"
            f"╚══════════════════════════════════════════╝\n"
            f"Type 'help' for available commands.\n"
        )

    def _start_shell(self):
        """Start shell inside podman container."""
        engine    = self._config.get("container_engine", "podman")
        container = self._config.get("container_name", "cybersec-mode-env")
        shell     = self._config.get("shell", "bash")

        if shutil.which(engine):
            cmd = [engine, "exec", "-it", container, shell]
        else:
            cmd = [shell]

        self._shell = ShellProcess(cmd)
        self._shell.output.connect(self._append)
        self._shell.finished.connect(lambda rc: self._append(f"\n[Process exited: {rc}]"))
        self._shell.start()

    def _submit(self):
        cmd = self.input_line.text().strip()
        if not cmd:
            return
        self._history.append(cmd)
        self._hist_idx = len(self._history)
        self.input_line.clear()
        self._append(f"$ {cmd}")

        if cmd == "clear":
            self._clear()
            return

        if self._shell and self._shell.isRunning():
            self._shell.write(cmd)
        else:
            self._start_shell()
            if self._shell:
                self._shell.write(cmd)

    def _append(self, text: str):
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        self.output.insertPlainText(text + "\n")
        self.output.moveCursor(QTextCursor.MoveOperation.End)

    def _clear(self):
        self.output.clear()

    def run_command(self, cmd: str):
        self.input_line.setText(cmd)
        self._submit()

    def eventFilter(self, obj, event):
        if obj == self.input_line and event.type() == event.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up and self._history:
                self._hist_idx = max(0, self._hist_idx - 1)
                self.input_line.setText(self._history[self._hist_idx])
            elif key == Qt.Key.Key_Down:
                self._hist_idx = min(len(self._history), self._hist_idx + 1)
                if self._hist_idx < len(self._history):
                    self.input_line.setText(self._history[self._hist_idx])
                else:
                    self.input_line.clear()
        return super().eventFilter(obj, event)

    def on_mode_changed(self, mode: str):
        pass  # terminal is mode-agnostic


class TerminalPanel(QWidget):
    """Panel containing multiple terminal tabs / split view."""

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._terminals: list[TerminalWidget] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar + add button
        tab_bar = QFrame()
        tab_bar.setFixedHeight(36)
        tab_bar.setStyleSheet("background: #111; border-bottom: 1px solid #1e1e1e;")
        tab_l = QHBoxLayout(tab_bar)
        tab_l.setContentsMargins(8, 0, 8, 0)
        tab_l.setSpacing(4)

        self._tab_label = QLabel("Terminal 1")
        self._tab_label.setStyleSheet(
            "color: #22c55e; font-size: 12px; font-weight: 700; "
            "background: #1e1e1e; padding: 4px 12px; border-radius: 3px;"
        )
        tab_l.addWidget(self._tab_label)
        tab_l.addStretch()

        btn_new = QPushButton("+ New")
        btn_new.setFixedHeight(26)
        btn_new.setStyleSheet(
            "background: #1e1e1e; border: 1px solid #2e2e2e; "
            "color: #666; font-size: 11px; border-radius: 3px; padding: 0 10px;"
        )
        btn_new.clicked.connect(self._new_terminal)
        tab_l.addWidget(btn_new)

        layout.addWidget(tab_bar)

        # Terminal widget
        self._term = TerminalWidget("cybersec-mode-env", self._config)
        layout.addWidget(self._term)
        self._terminals.append(self._term)

    def _new_terminal(self):
        # Placeholder: in production would open new tab/split
        self._term.run_command("echo '[New terminal session]'")

    def run_command(self, cmd: str):
        self._term.run_command(cmd)

    @pyqtSlot(str)
    def on_mode_changed(self, mode: str):
        for t in self._terminals:
            t.on_mode_changed(mode)
