# bridge.py
# Bridge: performs compile/upload + serial communication ON a specific Board.
# Modes:
#  - "local"  – uses arduino-cli and local pyserial (Board.serial)
#  - "remote" – HTTP/WS client (RemoteBackend)
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

DEFAULT_REMOTE_URL = "http://localhost:5000"  # default remote server URL (for REMOTE_MODE)

class Bridge:
    """
    Performs operations on a specific board (Board), locally or remotely.

    Attributes:
        mode (str): Operation mode ("local" or "remote").
        _be (Backend): Backend instance (LocalBackend or RemoteBackend).
        _printer (Callable[[str], None]): Printer function for output.
    """
    def __init__(
        self,
        mode: str = LOCAL_MODE,
        remote_url: Optional[str] = DEFAULT_REMOTE_URL,
        token: Optional[str] = None,
        explicit_printer: Optional[Callable[[str], None]] = None
    ):
        """
        Initializes the Bridge.

        Args:
            mode (str): Operation mode ("local" or "remote").
            remote_url (Optional[str]): Remote server URL for REMOTE_MODE.
            token (Optional[str]): API token for remote mode.
            explicit_printer (Optional[Callable[[str], None]]): Custom printer function.

        Raises:
            ValueError: If mode is not valid or required parameters are missing.
        """
        try:
            self.set_mode(mode, remote_url=remote_url, token=token)
        except ValueError as e:
            raise ValueError(f"Failed to initialize Bridge: {e}")
        self._printer: Callable[[str], None] = explicit_printer if explicit_printer else print

    # ---------- Wiring / configuration ----------
    def set_mode(
        self,
        mode: str,
        remote_url: Optional[str] = DEFAULT_REMOTE_URL,
        token: Optional[str] = None
    ) -> None:
        """
        Sets the work mode (local/remote) and initializes the backend.

        Args:
            mode (str): "local" or "remote".
            remote_url (Optional[str]): Remote server URL for REMOTE_MODE.
            token (Optional[str]): API token for remote mode.

        Raises:
            ValueError: If mode is not valid or required parameters are missing.
        """
        mode = mode.lower().strip()
        if mode not in (LOCAL_MODE, REMOTE_MODE):
            raise ValueError(f"Invalid mode '{mode}'. Use '{LOCAL_MODE}' or '{REMOTE_MODE}'.")
        self.mode = mode

        if self.mode == LOCAL_MODE:
            self._be: Backend = LocalBackend(arduino_cli=ARDUINO_CLI_PATH)
        else:  # REMOTE_MODE
            if not remote_url:
                remote_url = DEFAULT_REMOTE_URL
                print(f"⚠️ Warning: No remote_url provided, using default '{DEFAULT_REMOTE_URL}'")
            if not token:
                raise ValueError("API token must be provided for remote mode.")
            self._be: Backend = RemoteBackend(remote_url, token)

    def compile(
        self,
        board: Board,
        sketch_source: str,
        extra_args: Optional[Iterable[str]] = None,
        log_file: Optional[str] = None
    ) -> bool:
        """
        Compiles the sketch for the given board.

        Args:
            board (Board): The board to compile for.
            sketch_source (str): Path to the sketch directory (must be a directory).
            extra_args (Optional[Iterable[str]]): Additional CLI arguments.
            log_file (Optional[str]): Path to log file.

        Returns:
            bool: True if compilation is successful, False otherwise.

        Raises:
            ValueError: If sketch_source is not a directory.
            Exception: If backend compile fails.
        """
        if not os.path.isdir(sketch_source):
            raise ValueError(f"Sketch source '{sketch_source}' must be a directory!")
        self._printer(f"💻 **Compiling for {board.name} on port {board.port or 'N/A'}...**")
        self._printer("⏳ This may take a while, please wait...")

        try:
            res = self._be.compile(board, sketch_source, extra_args)
            ok = res.get("status", False)
            if ok:
                self._printer(res.get("stdout", ""))
                self._printer("✅ **Compile complete.**")
            else:
                self._printer(res.get("stderr", ""))
                self._printer("❌ **Compile failed.**")
            if log_file and isinstance(log_file, str):
                self._append_log(
                    log_file,
                    res.get("cmd", []),
                    res.get("stdout", ""),
                    res.get("stderr", ""),
                    res.get("ok", False)
                )
            return ok
        except Exception as e:
            raise e

    def upload(
        self,
        board: Board,
        sketch_source: str,
        extra_args: Optional[Iterable[str]] = None,
        log_file: Optional[str] = None
    ) -> bool:
        """
        Uploads the sketch to the given board.

        Args:
            board (Board): The board to upload to.
            sketch_source (str): Path to the sketch directory (must be a directory).
            extra_args (Optional[Iterable[str]]): Additional CLI arguments.
            log_file (Optional[str]): Path to log file.

        Returns:
            bool: True if upload is successful, False otherwise.

        Raises:
            ValueError: If sketch_source is not a directory.
            Exception: If backend upload fails.
        """
        if not os.path.isdir(sketch_source):
            raise ValueError(f"Sketch source '{sketch_source}' must be a directory!")
        self._printer(f"📡 **Uploading to {board.name} on port {board.port or 'N/A'}...**")
        self._printer("⏳ This may take a while, please wait...")
        try:
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
                self._append_log(
                    log_file,
                    res.get("cmd", []),
                    res.get("stdout", ""),
                    res.get("stderr", ""),
                    res.get("ok", False)
                )
            return ok
        except Exception as e:
            raise e

    def open_serial(self, board: Board) -> None:
        """
        Opens the serial port for the given board.

        Args:
            board (Board): The board whose serial port to open.

        Raises:
            Exception: If opening the serial port fails.
        """
        try:
            self._be.open_serial(board)
        except Exception as e:
            raise RuntimeError(f"Failed to open serial port: {e}")

    def close_serial(self, board: Board) -> None:
        """
        Closes the serial port for the given board.

        Args:
            board (Board): The board whose serial port to close.

        Raises:
            Exception: If closing the serial port fails.
        """
        try:
            self._be.close_serial(board)
        except Exception as e:
            raise RuntimeError(f"Failed to close serial port: {e}")

    def read_serial(self, board: Board, size: int = 1024) -> bytes:
        """
        Reads bytes from the serial port.

        Args:
            board (Board): The board whose serial port to read from.
            size (int): Number of bytes to read.

        Returns:
            bytes: Bytes read from the serial port.

        Raises:
            Exception: If reading from serial fails.
        """
        try:
            return self._be.read_serial(board, size)
        except Exception as e:
            raise RuntimeError(f"Failed to read from serial port: {e}")

    def readlines_serial(self, board: Board, size: int = 1) -> List[str]:
        """
        Reads lines from the serial port.

        Args:
            board (Board): The board whose serial port to read from.
            size (int): Number of lines to read.

        Returns:
            List[str]: List of lines read from the serial port.

        Raises:
            Exception: If reading lines from serial fails.
        """
        try:
            return self._be.readlines_serial(board, size)
        except Exception as e:
            raise RuntimeError(f"Failed to read lines from serial port: {e}")

    def write_serial(self, board: Board, data: Union[bytes, str], append_newline: bool = True) -> int:
        """
        Writes data to the serial port.

        Args:
            board (Board): The board whose serial port to write to.
            data (Union[bytes, str]): Data to write.
            append_newline (bool): Whether to append a newline.

        Returns:
            int: Number of bytes written.

        Raises:
            Exception: If writing to serial fails.
        """
        try:
            return self._be.write_serial(board, data, append_newline)
        except Exception as e:
            raise RuntimeError(f"Failed to write to serial port: {e}")

    def listen_serial(
        self,
        board: Board,
        duration: Optional[int] = None,
        prefix: Optional[str] = None,
        filters: List[str] = [""]
    ) -> None:
        """
        Listens to the serial port and prints lines, optionally filtering by prefix and duration.

        Args:
            board (Board): The board whose serial port to listen to.
            duration (Optional[int]): Duration in seconds to listen (None for unlimited).
            prefix (Optional[str]): Only print lines starting with this prefix.
            filters (List[str]): List of lines to ignore.

        Raises:
            Exception: If listening fails.
        """
        start = time.time()
        try:
            while True:
                if duration is not None and (time.time() - start) >= duration:
                    break
                lines = self.readlines_serial(board, size=1)
                line = lines[0] if lines else None
                if line is None or line in filters:
                    continue
                if prefix is not None and not line.startswith(prefix):
                    continue
                self._printer(line)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise RuntimeError(f"Error during serial listen: {e}")

    @staticmethod
    def _append_log(
        log_file: str,
        cmd: list[str],
        stdout: str,
        stderr: str,
        ok: bool
    ) -> None:
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