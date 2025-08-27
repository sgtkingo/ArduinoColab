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
    """Lokální adaptér – používej přímo tvůj kernel/arduino-cli a Board.serial."""
    def __init__(self, arduino_cli: str|None = None):
        self._cli_path: str = arduino_cli if arduino_cli else self._resolve_cli()           
        
    def set_cli_path(self, cli_path:str) -> None:
        """
        Optionally set a fixed path to arduino-cli (overrides autodetection).

        Args:
            cli_path (Optional[str]): Path to arduino-cli executable.
        """
        self._cli_path = cli_path
        
    # --- pomocná funkce pro CLI; nahraď přímým voláním kernelu, pokud ho máš ---
    def _run_cli(self, cmd: List[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def compile(self, board: Board, sketch_source: str,
                extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        # Kompilace využívá board.fqbn; port není nutný.
        with tempfile.TemporaryDirectory() as td:
            sketch_dir = os.path.join(td, "sketch")
            os.makedirs(sketch_dir, exist_ok=True)
            ino_path = os.path.join(sketch_dir, "sketch.ino")
            with open(ino_path, "w", encoding="utf-8") as f:
                f.write(sketch_source)
                
            cmd = [
                self._cli_path, "upload",
                ino_path,
                "-b", board.fqbn,
            ]
            if extra_args:
                cmd.extend(extra_args)
            proc = self._run_cli(cmd)
            status = True if proc.returncode == 0 else False
            return {"status": status, "stdout": proc.stdout, "stderr": proc.stderr}

    def upload(self, board: Board, sketch_source: str,
               extra_args: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        # Upload využije board.fqbn a board.port – vše je uvnitř Boardu.
        with tempfile.TemporaryDirectory() as td:
            sketch_dir = os.path.join(td, "sketch")
            os.makedirs(sketch_dir, exist_ok=True)
            ino_path = os.path.join(sketch_dir, "sketch.ino")
            with open(ino_path, "w", encoding="utf-8") as f:
                f.write(sketch_source)
            
            if board.port is None:
                raise RuntimeError("No serial port is set for the board. Use `%board serial` to set it.")
            cmd = [
                self._cli_path, "upload",
                ino_path,
                "-p", board.port,
                "-b", board.fqbn,
            ]
            if extra_args:
                cmd.extend(extra_args)

            proc = self._run_cli(cmd)
            status = True if proc.returncode == 0 else False
            return {"status": status, "stdout": proc.stdout, "stderr": proc.stderr}

    def open_serial(self, board: Board) -> None:
        # Využij kompozici: board.serial už zná port/baud/timeout z configure()
        # Pokud tvůj SerialPort vyžaduje explicitní open(), zavolej jej:
        if hasattr(board.serial, "open"):
            board.serial.open()  # otevře podle uložené konfigurace

    def close_serial(self, board: Board) -> None:
        if hasattr(board.serial, "close"):
            board.serial.close()

    def read_serial(self, board: Board, size: int = -1) -> bytes:
        # Čtení přes SerialPort – respektuje timeout a encoding řeší až volající (pokud chce text)
        return board.serial.read(size)
    
    def readlines_serial(self, board: Board, size: int = 1) -> List[str]:
        # Čtení přes SerialPort – respektuje timeout a encoding řeší až volající (pokud chce text)
        return board.serial.readlines(size)

    def write_serial(self, board: Board, data: Union[bytes, str], append_newline: bool = True) -> int:
        # Zápis přepošli na SerialPort – pokud je str, SerialPort si poradí dle své konfigurace
        return board.serial.write(data, append_newline)

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