# board_manager.py
# Management of selection and uploading to supported Arduino boards (Uno, Nano)
# Requires installation of arduino-cli and the appropriate toolchain.

from __future__ import annotations
import subprocess
import os
from typing import Optional, Tuple, Dict

import importlib.resources as pkg_resources
try:
    from arduino_colab_kernel import tools  # folder with arduino-cli in the package
except Exception:
    tools = None  # fallback if tools is not part of the package
    
from arduino_colab_kernel.board.board import Board

SUPPORTED_BOARDS = {
    "uno":  "arduino:avr:uno",
    "nano": "arduino:avr:nano",
}

DEFAULT_BOARD = "uno"

def _append_log(log_file: str, cmd: list[str], stdout: str, stderr: str, ok: bool):
    """Appends the compile/upload log to a file."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    except Exception:
        pass
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n" + "="*80 + "\n")
        f.write(("OK" if ok else "FAIL") + " | " + " ".join(cmd) + "\n")
        if stdout:
            f.write("\n[STDOUT]\n" + stdout.strip() + "\n")
        if stderr:
            f.write("\n[STDERR]\n" + stderr.strip() + "\n")

class BoardManager:
    def __init__(self):
        self.board: Optional[Board] = None
        self.default()

    # ---------- Board selection ----------
    def default(self):
        """Set the default board and automatic port."""
        self.select_board(DEFAULT_BOARD)
    
    def list_boards(self) -> Dict[str, str]:
        """
        Returns a list of supported boards as pairs (name, FQBN).
        """
        return SUPPORTED_BOARDS

    def select_board(self, name: str):
        key = name.strip().lower()
        if key not in SUPPORTED_BOARDS:
            raise ValueError(f"Board '{name}' is not supported. Supported: {list(SUPPORTED_BOARDS.keys())}")
        self.board = Board(name=key, fqbn=SUPPORTED_BOARDS[key])

    def require_board(self) -> Board:
        if not self.board:
            raise RuntimeError("No board is set. Call set_board('uno'|'nano').")
        return self.board

    # ---------- Board configuration ----------

    def configure(self, **kwargs):
        self.require_board().configure(**kwargs)
    
    def export(self) -> dict:
        # Returns the configuration of the current board and serial port as a dictionary
        b = self.require_board()
        if not b:
            return {}
        
        return {
            "name": b.name,
            "fqbn": b.fqbn,
            "port": b.port,
            "serial":
                    {
                        "baudrate": b.serial.baudrate,
                        "timeout": b.serial.timeout,
                        "encoding": b.serial.encoding,
                        "autostrip": b.serial.autostrip  
                    }
        } 

# Singleton for magics
board_manager = BoardManager()