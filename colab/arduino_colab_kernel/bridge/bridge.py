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
    """
    Performs operations on a specific board (Board), locally or remotely.

    Attributes:
        mode (str): Operation mode ("local" or "remote").
        _cli_path (Optional[str]): Optional fixed path to arduino-cli.
    """

    def __init__(self, mode: str = LOCAL_MODE):
        """
        Initializes the Bridge.

        Args:
            mode (str): Operation mode ("local" or "remote").

        Raises:
            ValueError: If mode is not valid.
        """
        self.mode = mode.lower().strip()
        self._cli_path: Optional[str] = None

    # ---------- Wiring / configuration ----------
    def set_mode(self, mode: str) -> None:
        """
        Sets the work mode (local/remote).

        Args:
            mode (str): "local" or "remote".

        Raises:
            ValueError: If mode is not valid.
        """
        mode = mode.lower().strip()
        if mode not in (LOCAL_MODE, REMOTE_MODE):
            raise ValueError(f"Invalid mode '{mode}'. Use '{LOCAL_MODE}' or '{REMOTE_MODE}'.")
        self.mode = mode

    def set_cli_path(self, cli_path: Optional[str]) -> None:
        """
        Optionally set a fixed path to arduino-cli (overrides autodetection).

        Args:
            cli_path (Optional[str]): Path to arduino-cli executable.
        """
        self._cli_path = cli_path

    # ---------- Compile / Upload ----------
    def compile(self, sketch_path: str, log_file: Optional[str] = None) -> bool:
        """
        Compiles the sketch in the given directory for the current board.

        Args:
            sketch_path (str): Path to the folder with the .ino file.
            log_file (Optional[str]): Path to log file.

        Returns:
            bool: True if compilation is successful.

        Raises:
            RuntimeError: If no serial port is set, or compilation fails.
            Exception: If subprocess or file operations fail.
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
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:
            raise RuntimeError(f"Failed to run compile command: {e}")
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

        Args:
            sketch_path (str): Path to the folder with the .ino file.
            log_file (Optional[str]): Path to log file.

        Returns:
            bool: True if upload is successful.

        Raises:
            RuntimeError: If no serial port is set, or upload fails.
            Exception: If subprocess or file operations fail.
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
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:
            raise RuntimeError(f"Failed to run upload command: {e}")
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
        """
        Opens the serial port according to Board.serial configuration.

        Raises:
            RuntimeError: If board or serial port is not available.
            Exception: If serial open fails.
        """
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_open()
        if not b.serial:
            raise RuntimeError("Board does not have an attached SerialPort.")
        try:
            b.serial.open()
        except Exception as e:
            raise RuntimeError(f"Failed to open serial port: {e}")

    def close_serial(self) -> None:
        """
        Closes the serial port.

        Raises:
            Exception: If serial close fails.
        """
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_close()
        if b.serial:
            try:
                b.serial.close()
            except Exception as e:
                raise RuntimeError(f"Failed to close serial port: {e}")

    def serial_listen(self, duration: Optional[float] = None, prefix: Optional[str] = None) -> None:
        """
        Streams serial output (LOCAL: delegates to Board.serial.listen).

        Args:
            duration (Optional[float]): Listening duration in seconds.
            prefix (Optional[str]): Only lines starting with this prefix are printed.

        Raises:
            Exception: If serial listen fails.
        """
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_listen(duration, prefix)
        try:
            b.serial.listen(duration=duration, prefix=prefix, printer=print)
        except Exception as e:
            raise RuntimeError(f"Failed during serial listen: {e}")

    def serial_read(self, lines: int = 1) -> list[str]:
        """
        Reads N lines (LOCAL: delegates to Board.serial.read).

        Args:
            lines (int): Number of lines to read.

        Returns:
            list[str]: List of lines read from serial.

        Raises:
            Exception: If serial read fails.
        """
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_read(lines)
        try:
            return b.serial.read(lines=lines)
        except Exception as e:
            raise RuntimeError(f"Failed during serial read: {e}")

    def serial_write(self, data: str, append_newline: bool = True) -> None:
        """
        Writes data (LOCAL: delegates to Board.serial.write).

        Args:
            data (str): Data to write to serial.
            append_newline (bool): Whether to append a newline.

        Raises:
            Exception: If serial write fails.
        """
        b = board_manager.require_board()
        if self.mode == "remote":
            return self._remote_serial_write(data, append_newline)
        try:
            b.serial.write(data, append_newline=append_newline)
        except Exception as e:
            raise RuntimeError(f"Failed during serial write: {e}")

    # ---------- Internal helpers ----------

    def _resolve_cli(self) -> str:
        """
        Finds the path to arduino-cli – prefers explicit, then resolver/utils, finally PATH.

        Returns:
            str: Path to arduino-cli executable.

        Raises:
            FileNotFoundError: If arduino-cli cannot be found.
        """
        if self._cli_path and Path(self._cli_path).exists():
            return self._cli_path
        return resolve_arduino_cli_path(ARDUINO_CLI_PATH)

    @staticmethod
    def _append_log(log_file: str, cmd: list[str], stdout: str, stderr: str, ok: bool) -> None:
        """
        Appends a run record to the log file.

        Args:
            log_file (str): Path to log file.
            cmd (list[str]): Command executed.
            stdout (str): Standard output.
            stderr (str): Standard error.
            ok (bool): Whether the command succeeded.

        Raises:
            Exception: If log file cannot be written.
        """
        try:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(("OK" if ok else "FAIL") + " | " + " ".join(cmd) + "\n")
                if stdout:
                    f.write("\n[STDOUT]\n" + stdout.strip() + "\n")
                if stderr:
                    f.write("\n[STDERR]\n" + stderr.strip() + "\n")
        except Exception as e:
            raise RuntimeError(f"Failed to write to log file '{log_file}': {e}")

    # ---------- Remote placeholders (not implemented yet) ----------

    def _remote_compile(self, sketch_dir_or_ino: str, log_file: Optional[str]) -> bool:
        """
        Placeholder for remote compile (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote compile not implemented yet.")

    def _remote_upload(self, sketch_dir_or_ino: str, log_file: Optional[str]) -> bool:
        """
        Placeholder for remote upload (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote upload not implemented yet.")

    def _remote_serial_open(self) -> None:
        """
        Placeholder for remote serial open (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote serial open not implemented yet.")

    def _remote_serial_close(self) -> None:
        """
        Placeholder for remote serial close (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote serial close not implemented yet.")

    def _remote_serial_listen(self, duration: Optional[float], prefix: Optional[str]) -> None:
        """
        Placeholder for remote serial listen (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote serial listen not implemented yet.")

    def _remote_serial_read(self, lines: int) -> list[str]:
        """
        Placeholder for remote serial read (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote serial read not implemented yet.")

    def _remote_serial_write(self, data: str, append_newline: bool) -> None:
        """
        Placeholder for remote serial write (not implemented).

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Remote serial write not implemented yet.")

bridge_manager = Bridge(mode=LOCAL_MODE)  # Global instance of the Bridge manager