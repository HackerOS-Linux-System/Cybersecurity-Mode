from __future__ import annotations
import os
import shutil
import subprocess
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QLineEdit, QFrame, QSizePolicy, QComboBox,
    QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QProcess
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

HSH_BIN   = "/usr/bin/hsh"
BASH_BIN  = "/bin/bash"
TERM_FONT = "JetBrains Mono, Fira Code, Cascadia Code, monospace"

TERM_OUTPUT_STYLE = f"""
QPlainTextEdit {{
    background-color: #0c0d0f;
    color: #c8ffc8;
    font-family: {TERM_FONT};
    font-size: 13px;
    border: none;
    padding: 10px 14px;
    selection-background-color: #1a3a1a;
    line-height: 1.4;
}}
"""

TERM_INPUT_STYLE = f"""
QLineEdit {{
    background-color: #0c0d0f;
    color: #22e87a;
    font-family: {TERM_FONT};
    font-size: 13px;
    border: none;
    border-top: 1px solid #1e2028;
    padding: 7px 12px;
}}
QLineEdit:focus {{ border-top-color: #2a2a38; }}
"""


class ShellWorker(QThread):
    """Runs a shell process, emits output lines."""
    line_received = pyqtSignal(str)
    process_ended = pyqtSignal(int)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self._cmd  = cmd
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def run(self):
        try:
            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["COLORTERM"] = "truecolor"

            self._proc = subprocess.Popen(
                self._cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
                errors="replace",
            )
            for line in iter(self._proc.stdout.readline, ""):
                self.line_received.emit(line.rstrip("\n"))
            self._proc.wait()
            self.process_ended.emit(self._proc.returncode)
        except FileNotFoundError as e:
            self.line_received.emit(f"[ERROR] Command not found: {e}")
            self.process_ended.emit(127)
        except Exception as e:
            self.line_received.emit(f"[ERROR] {e}")
            self.process_ended.emit(1)

    def send(self, text: str):
        with self._lock:
            if self._proc and self._proc.stdin and not self._proc.stdin.closed:
                try:
                    self._proc.stdin.write(text + "\n")
                    self._proc.stdin.flush()
                except BrokenPipeError:
                    pass

    def terminate(self):
        with self._lock:
            if self._proc:
                try:
                    self._proc.terminate()
                except Exception:
                    pass


class TerminalTab(QWidget):
    """A single terminal tab: output + input line."""

    def __init__(self, tab_id: int, config):
        super().__init__()
        self._id      = tab_id
        self._config  = config
        self._history: list[str] = []
        self._hist_i  = -1
        self._worker: ShellWorker | None = None

        self._build()
        self._start_shell()

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Output
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(TERM_OUTPUT_STYLE)
        self.output.setMaximumBlockCount(20_000)
        self.output.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.output)

        # Input row
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(0)

        self._prompt_label = QLabel()
        self._update_prompt()
        input_row.addWidget(self._prompt_label)

        self.input_line = QLineEdit()
        self.input_line.setStyleSheet(TERM_INPUT_STYLE)
        self.input_line.setPlaceholderText("")
        self.input_line.returnPressed.connect(self._submit)
        self.input_line.installEventFilter(self)
        input_row.addWidget(self.input_line)
        layout.addLayout(input_row)

        self._print_banner()

    def _update_prompt(self):
        mode  = self._config.get("mode", "red")
        shell = self._get_shell_name()
        color = "#ef4444" if mode == "red" else "#3b82f6"
        sym   = "⚔" if mode == "red" else "🛡"
        self._prompt_label.setText(f"  {sym} {shell} ❯  ")
        self._prompt_label.setStyleSheet(
            f"color: {color}; font-family: {TERM_FONT}; font-size: 13px; "
            f"background: #0c0d0f; padding: 7px 0 7px 12px; font-weight: 700;"
        )

    def _get_shell_name(self) -> str:
        shell = self._config.get("shell", "hsh")
        if shell == "hsh" and Path(HSH_BIN).exists():
            return "hsh"
        return "bash"

    def _print_banner(self):
        mode  = self._config.get("mode", "red")
        sym   = "⚔  RED MODE" if mode == "red" else "🛡  BLUE MODE"
        shell = HSH_BIN if Path(HSH_BIN).exists() else BASH_BIN
        self._append_plain(
            f"╔══════════════════════════════════════════════════════╗\n"
            f"║   Cybersecurity Mode v0.1  ─  {sym:<21}║\n"
            f"║   Container: blackarchlinux/blackarch                ║\n"
            f"║   Shell: {shell:<44}║\n"
            f"╚══════════════════════════════════════════════════════╝\n"
        )

    # ── Shell ─────────────────────────────────────────────────────────────

    def _build_cmd(self) -> list[str]:
        engine    = self._config.get("container_engine", "podman")
        container = self._config.get("container_name", "cybersec-mode-env")

        # Determine shell: prefer hsh
        if Path(HSH_BIN).exists():
            inner_shell = HSH_BIN
        else:
            inner_shell = BASH_BIN

        if shutil.which(engine):
            # Run inner_shell inside the container
            return [engine, "exec", "-it", container, inner_shell]
        else:
            # Fallback: run locally
            return [inner_shell]

    def _start_shell(self):
        cmd = self._build_cmd()
        self._append_plain(f"$ {' '.join(cmd)}\n\n")
        self._worker = ShellWorker(cmd)
        self._worker.line_received.connect(self._on_line)
        self._worker.process_ended.connect(self._on_exit)
        self._worker.start()

    @pyqtSlot(str)
    def _on_line(self, line: str):
        self._append_plain(line)

    @pyqtSlot(int)
    def _on_exit(self, code: int):
        self._append_plain(f"\n[Process exited: {code}]\n")

    # ── Input ─────────────────────────────────────────────────────────────

    def _submit(self):
        cmd = self.input_line.text()
        self.input_line.clear()
        if not cmd.strip():
            return

        self._history.append(cmd)
        self._hist_i = len(self._history)

        self._append_colored(f"❯ {cmd}", "#3a4a3a")

        # Handle built-ins
        if cmd.strip() == "clear":
            self.output.clear()
            return
        if cmd.strip() == "exit":
            if self._worker:
                self._worker.terminate()
            self._append_plain("\n[Session closed]\n")
            return

        if self._worker and self._worker.isRunning():
            self._worker.send(cmd)
        else:
            self._append_plain("[Shell not running — restarting…]\n")
            self._start_shell()
            if self._worker:
                QTimer.singleShot(500, lambda: self._worker.send(cmd) if self._worker else None)

    def _append_plain(self, text: str):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _append_colored(self, text: str, bg_color: str = ""):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        if bg_color:
            fmt.setForeground(QColor("#5a6a5a"))
        cursor.insertText(text + "\n", fmt)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def run_command(self, cmd: str):
        """External call to run a command programmatically."""
        self.input_line.setText(cmd)
        self._submit()

    def eventFilter(self, obj, event):
        if obj == self.input_line:
            if event.type() == event.Type.KeyPress:
                key = event.key()
                if key == Qt.Key.Key_Up and self._history:
                    self._hist_i = max(0, self._hist_i - 1)
                    self.input_line.setText(self._history[self._hist_i])
                    return True
                elif key == Qt.Key.Key_Down:
                    self._hist_i = min(len(self._history), self._hist_i + 1)
                    if self._hist_i < len(self._history):
                        self.input_line.setText(self._history[self._hist_i])
                    else:
                        self.input_line.clear()
                    return True
                elif key == Qt.Key.Key_L and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.output.clear()
                    return True
        return super().eventFilter(obj, event)

    @pyqtSlot(str)
    def on_mode_changed(self, mode: str):
        self._update_prompt()

    def closeEvent(self, event):
        if self._worker:
            self._worker.terminate()
        event.accept()


class TerminalPanel(QWidget):
    """
    Terminal panel — multiple tabs, tab management, shell info bar.
    Uses /usr/bin/hsh inside the BlackArch container.
    """

    def __init__(self, config):
        super().__init__()
        self._config   = config
        self._tabs: list[TerminalTab] = []
        self._current  = 0
        self._tab_count = 1
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tab bar ───────────────────────────────────────────────────────
        tab_bar = QFrame()
        tab_bar.setFixedHeight(38)
        tab_bar.setStyleSheet("QFrame { background: #0e0f12; border-bottom: 1px solid #1e2028; }")
        tbl = QHBoxLayout(tab_bar)
        tbl.setContentsMargins(8, 0, 8, 0)
        tbl.setSpacing(4)

        self._tab_buttons: list[QPushButton] = []
        self._tab_buttons_layout = tbl

        self._add_tab_btn("Terminal 1")

        tbl.addStretch()

        # Shell indicator
        shell_name = "hsh" if Path(HSH_BIN).exists() else "bash"
        lbl_shell = QLabel(f"  {shell_name}  ")
        lbl_shell.setStyleSheet(
            "color: #22c55e; font-size: 10px; font-weight: 700; font-family: monospace; "
            "background: #0a120a; border: 1px solid #22c55e33; border-radius: 3px; "
            "padding: 2px 0;"
        )
        lbl_shell.setToolTip(f"Shell: {HSH_BIN if shell_name == 'hsh' else BASH_BIN}")
        tbl.addWidget(lbl_shell)

        # New terminal button
        btn_new = QPushButton("＋")
        btn_new.setFixedSize(28, 26)
        btn_new.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #2a2a38; "
            "color: #555; border-radius: 4px; font-size: 14px; }"
            "QPushButton:hover { background: #1e1e28; color: #aaa; }"
        )
        btn_new.setToolTip("New terminal tab")
        btn_new.clicked.connect(self._new_tab)
        tbl.addWidget(btn_new)

        layout.addWidget(tab_bar)

        # ── Tab content area ───────────────────────────────────────────────
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        layout.addWidget(self._content)

        # Create first tab
        self._create_terminal()

    def _add_tab_btn(self, label: str) -> QPushButton:
        idx = len(self._tab_buttons)
        btn = QPushButton(label)
        btn.setFixedHeight(26)
        btn.setStyleSheet(self._tab_btn_style(active=idx == self._current))
        btn.clicked.connect(lambda _, i=idx: self._switch_tab(i))
        # Insert before the stretch
        insert_at = len(self._tab_buttons)
        self._tab_buttons_layout.insertWidget(insert_at, btn)
        self._tab_buttons.append(btn)
        return btn

    def _tab_btn_style(self, active: bool) -> str:
        if active:
            return (
                "QPushButton { background: #161820; border: 1px solid #2a2a38; "
                "color: #22c55e; border-radius: 4px; padding: 0 12px; "
                "font-size: 11px; font-weight: 700; }"
            )
        return (
            "QPushButton { background: transparent; border: 1px solid transparent; "
            "color: #444; border-radius: 4px; padding: 0 12px; font-size: 11px; }"
            "QPushButton:hover { background: #161820; color: #777; }"
        )

    def _create_terminal(self) -> TerminalTab:
        tab = TerminalTab(len(self._tabs), self._config)
        self._tabs.append(tab)
        self._content_layout.addWidget(tab)

        if len(self._tabs) > 1:
            tab.hide()

        return tab

    def _new_tab(self):
        self._tab_count += 1
        label = f"Terminal {self._tab_count}"
        self._add_tab_btn(label)
        tab = self._create_terminal()
        self._switch_tab(len(self._tabs) - 1)

    def _switch_tab(self, idx: int):
        if idx < 0 or idx >= len(self._tabs):
            return
        # Hide current
        if self._current < len(self._tabs):
            self._tabs[self._current].hide()
        if self._current < len(self._tab_buttons):
            self._tab_buttons[self._current].setStyleSheet(self._tab_btn_style(active=False))

        # Show new
        self._current = idx
        self._tabs[idx].show()
        self._tab_buttons[idx].setStyleSheet(self._tab_btn_style(active=True))

    def run_command(self, cmd: str):
        """Run command in the current tab."""
        if self._tabs:
            self._tabs[self._current].run_command(cmd)

    @pyqtSlot(str)
    def on_mode_changed(self, mode: str):
        for tab in self._tabs:
            tab.on_mode_changed(mode)
