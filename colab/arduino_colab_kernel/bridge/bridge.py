# bridge.py
# Bridge: performs compile/upload + serial communication ON a specific Board.
# Modes:
#  - "local"  – uses arduino-cli and local pyserial (Board.serial)
#  - "remote" – placeholders for future HTTP/WS client (not implemented)
from __future__ import annotations
from typing import Optional, Iterable
import os
import shutil
import subprocess
from pathlib import Path

from arduino_colab_kernel.utils.utils_cli import resolve_arduino_cli_path
from arduino_colab_kernel.board.board_manager import board_manager  # global instance BoardManager

# Local path to arduino-cli (can be in PATH or in the package)
ARDUINO_CLI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "arduino-cli.exe")
)

LOCAL_MODE = "local"  # local mode (default)
REMOTE_MODE = "remote"  # remote mode (e.g. for cloud IDEs)

class Bridge:
    """Performs operations on a specific board (Board), locally or remotely."""

    def __init__(self, mode: str = LOCAL_MODE):
        # Work mode ("local" | "remote")
        self.mode = mode.lower().strip()
        # Optional fixed path to arduino-cli (overrides autodetection)
        self._cli_path: Optional[str] = None

    # ---------- Wiring / configuration ----------
    def set_mode(self, mode: str) -> None:
        """Sets the work mode (local/remote)."""
        mode = mode.lower().strip()
        if mode not in (LOCAL_MODE, REMOTE_MODE):
            raise ValueError(f"Invalid mode '{mode}'. Use '{LOCAL_MODE}' or '{REMOTE_MODE}'.")
        self.mode = mode

    def set_cli_path(self, cli_path: Optional[str]) -> None:
        """Optionally set a fixed path to arduino-cli (overrides autodetection)."""
        self._cli_path = cli_path

    # ---------- Compile / Upload ----------
    def compile(self, sketch_path: str, log_file: Optional[str] = None) -> bool:
        """
        Compiles the sketch in the given directory for the current board.
        sketch_path: path to the folder with the .ino file
        Returns True if compilation is successful, otherwise raises an exception.
        """
        if self.mode == REMOTE_MODE:
            return self._remote_compile(sketch_path, log_file)
        
        b = board_manager.require_board()
        if b.port is None:
            raise RuntimeError("No serial port is set for the board. Use `%board serial` to set it.")
        
        cli = self._resolve_cli()
        sketch_dir = os.path.abspath(sketch_path)
        cmd = [
            cli, "compile",
            sketch_dir,
            "-p", b.port,
            "-b", b.fqbn,
        ]
        print(f"Compiling: {' '.join(cmd)}")  # Debug output
        result = subprocess.run(cmd, capture_output=True, text=True)
        ok = (result.returncode == 0)
        if not ok:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Compile failed: {result.stderr}")
        print(result.stdout)
        
        if log_file:
            self._append_log(log_file, cmd, result.stdout, result.stderr, ok)
            
        return ok

    def upload(self, sketch_path: str, log_file: Optional[str] = None) -> bool:
        """
        Uploads the sketch to the selected board via the set port (e.g. 'COM3' or '/dev/ttyUSB0').
        Returns True if upload is successful, otherwise raises an exception.
        """
        if self.mode == REMOTE_MODE:
            return self._remote_upload(sketch_path, log_file)
        
        # First compile to ensure the code is valid
        if not self.compile(sketch_path):
            raise RuntimeError("The code was not successfully compiled, upload failed.")
        
        b = board_manager.require_board()
        if b.port is None:
            raise RuntimeError("No serial port is set for the board. Use `%board serial` to set it.")
        
        cli = self._resolve_cli()
        sketch_dir = os.path.abspath(sketch_path)
        cmd = [
            cli, "upload",
            sketch_dir,
            "-p", b.port,
            "-b", b.fqbn,
        ]
        print(f"Uploading: {' '.join(cmd)}")  # Debug output
        result = subprocess.run(cmd, capture_output=True, text=True)
        ok = (result.returncode == 0)
        if not ok:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Upload failed: {result.stderr}")
        print(result.stdout)
        
        if log_file:
            self._append_log(log_file, cmd, result.stdout, result.stderr, ok)
            
        return ok

    # ---------- Serial I/O (delegates to Board.serial in LOCAL mode) ----------

    def open_serial(self) -> None:
        """Opens the serial port according to Board.serial configuration."""
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_open()
        if not b.serial:
            raise RuntimeError("Board does not have an attached SerialPort.")
        b.serial.open()

    def close_serial(self) -> None:
        """Closes the serial port."""
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_close()
        if b.serial:
            b.serial.close()

    def serial_listen(self, duration: Optional[float] = None, prefix: Optional[str] = None) -> None:
        """Streams serial output (LOCAL: delegates to Board.serial.listen)."""
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_listen(duration, prefix)
        b.serial.listen(duration=duration, prefix=prefix, printer=print)

    def serial_read(self, lines: int = 1) -> list[str]:
        """Reads N lines (LOCAL: delegates to Board.serial.read)."""
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_read(lines)
        return b.serial.read(lines=lines)

    def serial_write(self, data: str, append_newline: bool = True) -> None:
        """Writes data (LOCAL: delegates to Board.serial.write)."""
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_write(data, append_newline)
        b.serial.write(data, append_newline=append_newline)

    # ---------- Internal helpers ----------

    def _resolve_cli(self) -> str:
        """Finds the path to arduino-cli – prefers explicit, then resolver/utils, finally PATH."""
        if self._cli_path and Path(self._cli_path).exists():
            return self._cli_path
        return resolve_arduino_cli_path(ARDUINO_CLI_PATH)

    @staticmethod
    def _append_log(log_file: str, cmd: list[str], stdout: str, stderr: str, ok: bool) -> None:
        """Appends a run record to the log file."""
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(("OK" if ok else "FAIL") + " | " + " ".join(cmd) + "\n")
            if stdout:
                f.write("\n[STDOUT]\n" + stdout.strip() + "\n")
            if stderr:
                f.write("\n[STDERR]\n" + stderr.strip() + "\n")

    # ---------- Remote placeholders (not implemented yet) ----------

    def _remote_compile(self, sketch_dir_or_ino: str, log_file: Optional[str]) -> bool:
        raise NotImplementedError("Remote compile not implemented yet.")

    def _remote_upload(self, sketch_dir_or_ino: str, log_file: Optional[str]) -> bool:
        raise NotImplementedError("Remote upload not implemented yet.")

    def _remote_serial_open(self) -> None:
        raise NotImplementedError("Remote serial open not implemented yet.")

    def _remote_serial_close(self) -> None:
        raise NotImplementedError("Remote serial close not implemented yet.")

    def _remote_serial_listen(self, duration: Optional[float], prefix: Optional[str]) -> None:
        raise NotImplementedError("Remote serial listen not implemented yet.")

    def _remote_serial_read(self, lines: int) -> list[str]:
        raise NotImplementedError("Remote serial read not implemented yet.")

    def _remote_serial_write(self, data: str, append_newline: bool) -> None:
        raise NotImplementedError("Remote serial write not implemented yet.")

bridge_manager = Bridge(mode=LOCAL_MODE)  # Global instance of the Bridge manager