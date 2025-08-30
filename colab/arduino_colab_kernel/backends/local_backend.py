# backends/local_backend.py
from __future__ import annotations
import os, tempfile, subprocess
from pathlib import Path
from typing import Optional, Iterable, Dict, Any, Union, List

from arduino_colab_kernel.backends.protocol import Backend
from arduino_colab_kernel.board.board import Board
from arduino_colab_kernel.utils.utils_cli import resolve_arduino_cli_path

# Local path to arduino-cli (can be in PATH or in the package)
ARDUINO_CLI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "arduino-cli.exe")
)

class LocalBackend(Backend):
    """
    Local adapter – uses your kernel/arduino-cli and Board.serial directly.

    Attributes:
        _cli_path (str): Path to the arduino-cli executable.
    """
    def __init__(self, arduino_cli: str|None = None):
        """
        Initializes the LocalBackend.

        Args:
            arduino_cli (str|None): Optional explicit path to arduino-cli.

        Raises:
            FileNotFoundError: If arduino-cli cannot be found.
        """
        self._cli_path: str = arduino_cli if arduino_cli else self._resolve_cli()           
        
    def set_cli_path(self, cli_path:str) -> None:
        """
        Optionally set a fixed path to arduino-cli (overrides autodetection).

        Args:
            cli_path (str): Path to arduino-cli executable.
        """
        self._cli_path = cli_path
        
    def _run_cli(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """
        Runs a CLI command using subprocess.

        Args:
            cmd (List[str]): Command and arguments as a list.

        Returns:
            subprocess.CompletedProcess: The result of the subprocess run.

        Raises:
            RuntimeError: If the subprocess fails to run.
        """
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to run CLI command: {e}")

    def compile(self, board: Board, sketch_source: str,
                extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """
        Compiles the sketch for the given board.

        Args:
            board (Board): The board to compile for.
            sketch_source (str): Path to the sketch directory or .ino file.
            extra_args (Optional[Iterable[str]]): Additional CLI arguments.

        Returns:
            Dict[str, Any]: Dictionary with 'status', 'stdout', and 'stderr'.

        Raises:
            Exception: If the compile command fails.
        """
        cli = self._cli_path
        sketch_dir = os.path.abspath(sketch_source)
        cmd = [
            cli, "compile",
            sketch_dir,
            "-b", board.fqbn,
        ]
        if extra_args:
            cmd.extend(extra_args)
        proc = self._run_cli(cmd)
        status = True if proc.returncode == 0 else False
        return {"status": status, "stdout": proc.stdout, "stderr": proc.stderr}

    def upload(self, board: Board, sketch_source: str,
               extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        """
        Uploads the sketch to the given board.

        Args:
            board (Board): The board to upload to.
            sketch_source (str): Path to the sketch directory or .ino file.
            extra_args (Optional[Iterable[str]]): Additional CLI arguments.

        Returns:
            Dict[str, Any]: Dictionary with 'status', 'stdout', and 'stderr'.

        Raises:
            RuntimeError: If no serial port is set for the board.
            Exception: If the upload command fails.
        """
        if board.port is None:
            raise RuntimeError("No serial port is set for the board. Use `%board serial` to set it.")
        cli = self._cli_path
        sketch_dir = os.path.abspath(sketch_source)
        cmd = [
            cli, "upload",
            sketch_dir,
            "-p", board.port,
            "-b", board.fqbn,
        ]
        if extra_args:
            cmd.extend(extra_args)
        proc = self._run_cli(cmd)
        status = True if proc.returncode == 0 else False
        return {"status": status, "stdout": proc.stdout, "stderr": proc.stderr}

    def open_serial(self, board: Board) -> None:
        """
        Opens the serial port for the given board.

        Args:
            board (Board): The board whose serial port to open.

        Raises:
            RuntimeError: If opening the serial port fails.
        """
        if hasattr(board.serial, "open"):
            try:
                board.serial.open()  # opens according to stored configuration
            except Exception as e:
                raise RuntimeError(f"Failed to open serial port: {e}")

    def close_serial(self, board: Board) -> None:
        """
        Closes the serial port for the given board.

        Args:
            board (Board): The board whose serial port to close.

        Raises:
            RuntimeError: If closing the serial port fails.
        """
        if hasattr(board.serial, "close"):
            try:
                board.serial.close()
            except Exception as e:
                raise RuntimeError(f"Failed to close serial port: {e}")

    def read_serial(self, board: Board, size: int = -1) -> bytes:
        """
        Reads bytes from the serial port.

        Args:
            board (Board): The board whose serial port to read from.
            size (int): Number of bytes to read (-1 for all available).

        Returns:
            bytes: Bytes read from the serial port.

        Raises:
            Exception: If reading from serial fails.
        """
        try:
            return board.serial.read(size)
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
            return board.serial.readlines(size)
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
            return board.serial.write(data, append_newline)
        except Exception as e:
            raise RuntimeError(f"Failed to write to serial port: {e}")

    # ---------- Internal helpers ----------

    def _resolve_cli(self) -> str:
        """
        Finds the path to arduino-cli – prefers explicit, then resolver/utils, finally PATH.

        Returns:
            str: Path to arduino-cli executable.

        Raises:
            FileNotFoundError: If arduino-cli cannot be found.
        """
        if hasattr(self, "_cli_path") and self._cli_path and Path(self._cli_path).exists():
            return self._cli_path
        return resolve_arduino_cli_path(ARDUINO_CLI_PATH)