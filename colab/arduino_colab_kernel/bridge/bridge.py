# bridge.py
# Bridge: performs compile/upload + serial communication ON a specific Board.
# Modes:
#  - "local"  – uses arduino-cli and local pyserial (Board.serial)
#  - "remote" – placeholders for future HTTP/WS client (not implemented)
from __future__ import annotations
from typing import Optional, Iterable, Dict, Any, Union, List, Callable
import os, time

from arduino_colab_kernel.backends.protocol import Backend
from arduino_colab_kernel.backends.local_backend import LocalBackend
from arduino_colab_kernel.backends.remote_backend import RemoteBackend

from arduino_colab_kernel.board.board import Board

# Local path to arduino-cli (can be in PATH or in the package)
ARDUINO_CLI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "arduino-cli.exe")
)

LOCAL_MODE = "local"  # local mode (default)
REMOTE_MODE = "remote"  # remote mode (e.g. for cloud IDEs)

BASE_URL = "http://localhost:5000"  # default remote server URL (for REMOTE_MODE)

class Bridge:
    """
    Performs operations on a specific board (Board), locally or remotely.

    Attributes:
        mode (str): Operation mode ("local" or "remote").
    """
    def __init__(self, mode: str = LOCAL_MODE, base_url: Optional[str] = BASE_URL, token: Optional[str] = None, explicit_printer: Optional[Callable[[str], None]] = None):
        """
        Initializes the Bridge.

        Args:
            mode (str): Operation mode ("local" or "remote").

        Raises:
            ValueError: If mode is not valid.
        """
        try:
            self.set_mode(mode, base_url=base_url, token=token)
        except ValueError as e:
            raise ValueError(f"Failed to initialize Bridge: {e}")
        
        self._printer:Callable[[str]] = explicit_printer if explicit_printer else print
            
        
    # ---------- Wiring / configuration ----------
    def set_mode(self, mode: str, base_url: Optional[str] = BASE_URL, token: Optional[str] = None) -> None:
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
        
        if self.mode == LOCAL_MODE:
            self._be: Backend = LocalBackend(arduino_cli=ARDUINO_CLI_PATH)
        else:  # REMOTE_MODE
            if not base_url or not token:
                raise ValueError("base_url and token must be provided for remote mode.")
            self._be: Backend = RemoteBackend(base_url=base_url, token=token)

    def compile(self, board: Board, sketch_source: str,
                extra_args: Optional[Iterable[str]] = None, log_file:Optional[Iterable[str]] = None) -> bool:
        if not os.path.isdir(sketch_source):
            raise ValueError(f"Sketch source '{sketch_source}' must be a directory!")
        
        self._printer(f"💻 **Compiling for {board.name} on port {board.port or 'N/A'}...**")
        self._printer("⏳ This may take a while, please wait...")
        
        res = self._be.compile(board, sketch_source, extra_args)
        ok = res.get("status", False)
        if ok:
            self._printer(res.get("stdout", ""))
            self._printer("✅ **Compile complete.**")
        else:
            self._printer(res.get("stderr", ""))
            self._printer("❌ **Compile failed.**")
        if log_file and isinstance(log_file, str):
            self._append_log(log_file, res.get("cmd", []), res.get("stdout", ""), res.get("stderr", ""), res.get("ok", False))
        return ok

    def upload(self, board: Board, sketch_source: str,
               extra_args: Optional[Iterable[str]] = None, log_file:Optional[Iterable[str]] = None) -> bool:
        
        if not os.path.isdir(sketch_source):
            raise ValueError(f"Sketch source '{sketch_source}' must be a directory!")
        
        self._printer(f"📡 **Uploading to {board.name} on port {board.port or 'N/A'}...**")
        self._printer("⏳ This may take a while, please wait...")
        # First compile, then upload if successful
        if not self.compile(board, sketch_source, log_file=log_file, extra_args=extra_args):
            self._printer("❌ **Compilation failed, upload aborted.**")
            return False
            
        res = self._be.upload(board, sketch_source, extra_args)
        ok = res.get("status", False)
        if ok:
            self._printer(res.get("stdout", ""))
            self._printer("✅ **Upload complete.**")
        else:
            self._printer(res.get("stderr", ""))
            self._printer("❌ **Upload failed.**")
        if log_file and isinstance(log_file, str):
            self._append_log(log_file, res.get("cmd", []), res.get("stdout", ""), res.get("stderr", ""), res.get("ok", False))
        
        return ok

    def open_serial(self, board: Board) -> None:
        self._be.open_serial(board)

    def close_serial(self, board: Board) -> None:
        self._be.close_serial(board)
        
    def read_serial(self, board: Board, size: int = 1024) -> bytes:
        return self._be.read_serial(board, size)

    def readlines_serial(self, board: Board, size: int = 1) -> List[str]:
        return self._be.readlines_serial(board, size)

    def write_serial(self, board: Board, data: Union[bytes, str], append_newline: bool = True) -> int:
        return self._be.write_serial(board, data, append_newline)
    
    def listen_serial(self, board: Board, duration: Optional[int] = None,
                    prefix: Optional[str] = None) -> None:
        start = time.time()
        try:
            while True:
                if duration is not None and (time.time() - start) >= duration:
                    break
                line = self.readlines_serial(board, size=1)
                line = line[0] if line else None
                if line is None:
                    continue
                if prefix is not None and not line.startswith(prefix):
                    continue
                self._printer(line)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise RuntimeError(f"Error during serial listen: {e}")
    
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

bridge_manager = Bridge(mode=LOCAL_MODE)  # Global instance of the Bridge manager