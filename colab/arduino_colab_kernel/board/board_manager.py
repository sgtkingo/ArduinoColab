# board_manager.py
# Management of selection and uploading to supported Arduino boards (Uno, Nano)
# Requires installation of arduino-cli and the appropriate toolchain.

from __future__ import annotations
import os
from typing import Optional, Dict

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

class BoardManager:
    """
    Manages selection and configuration of supported Arduino boards.

    Attributes:
        board (Optional[Board]): The currently selected board.
    """
    def __init__(self):
        """
        Initializes the BoardManager and sets the default board.
        """
        self.board: Optional[Board] = None
        self.default()

    # ---------- Board selection ----------
    def default(self):
        """
        Set the default board and automatic port.

        Raises:
            ValueError: If the default board is not supported.
            RuntimeError: If the board cannot be initialized.
        """
        self.select_board(DEFAULT_BOARD)
    
    def list_boards(self) -> Dict[str, str]:
        """
        Returns a list of supported boards as pairs (name, FQBN).

        Returns:
            Dict[str, str]: Dictionary mapping board names to FQBNs.
        """
        return SUPPORTED_BOARDS

    def select_board(self, name: str):
        """
        Selects a board by name and initializes it.

        Args:
            name (str): Name of the board to select.

        Raises:
            ValueError: If the board name is not supported.
            RuntimeError: If the board cannot be initialized.
        """
        key = name.strip().lower()
        if key not in SUPPORTED_BOARDS:
            raise ValueError(f"Board '{name}' is not supported. Supported: {list(SUPPORTED_BOARDS.keys())}")
        try:
            self.board = Board(name=key, fqbn=SUPPORTED_BOARDS[key])
        except Exception as e:
            raise RuntimeError(f"Failed to initialize board '{name}': {e}")

    def require_board(self) -> Board:
        """
        Returns the currently selected board.

        Returns:
            Board: The currently selected Board instance.

        Raises:
            RuntimeError: If no board is set.
        """
        if not self.board:
            raise RuntimeError("No board is set. Call set_board('uno'|'nano').")
        return self.board

    # ---------- Board configuration ----------

    def configure(self, **kwargs):
        """
        Configures the current board with the provided keyword arguments.

        Args:
            **kwargs: Configuration parameters for the board.

        Raises:
            RuntimeError: If no board is set or configuration fails.
        """
        try:
            self.require_board().configure(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to configure board: {e}")
    
    def export(self) -> dict:
        """
        Returns the configuration of the current board and serial port as a dictionary.

        Returns:
            dict: Dictionary with board and serial configuration.

        Raises:
            RuntimeError: If no board is set.
        """
        b = self.require_board()
        if not b:
            return {}
        
        return b.export()

# Singleton for magics
board_manager = BoardManager()