# board_manager.py
# Správa výběru a nahrávání na podporované Arduino desky (Uno, Nano)
# Požaduje instalaci arduino-cli a příslušného toolchainu.

import subprocess
import os

ARDUINO_CLI_PATH = r"./tools/arduino-cli.exe"  # Cesta k arduino-cli, pokud není v PATH

class BoardManager:
    # Podporované desky a jejich fully-qualified board name (FQBN) pro arduino-cli
    SUPPORTED_BOARDS = {
        "uno": "arduino:avr:uno",
        "nano": "arduino:avr:nano"
    }

    def __init__(self):
        # Výchozí deska je None
        self.selected_board = None
        self.fqbn = None
        self.port = None 

    def select_board(self, board_name: str, port: str):
        """
        Nastaví aktuální desku podle zadaného jména.
        Povolené hodnoty: 'uno', 'nano'
        """
        board_key = board_name.strip().lower()
        if board_key not in self.SUPPORTED_BOARDS:
            raise ValueError(f"Deska '{board_name}' není podporována. Podporované: {list(self.SUPPORTED_BOARDS.keys())}")
        self.selected_board = board_key
        self.fqbn = self.get_fqbn()
        self.port = port

    def get_fqbn(self) -> str:
        """
        Vrací fully-qualified board name pro aktuální desku.
        """
        if not self.selected_board:
            raise RuntimeError("Není vybrána žádná deska.")
        return self.SUPPORTED_BOARDS[self.selected_board]
    
    def get_selected_board(self) -> tuple:
        """
        Vrací jméno aktuálně vybrané desky (např. 'uno', 'nano') a její příslušné fully-qualified board name a port na kterém je připojena.
        """
        return self.selected_board, self.fqbn, self.port
    
    def list_boards(self) -> list:
        """
        Vrací seznam podporovaných desek jako seznam dvojic (jméno, FQBN).
        """
        return list(self.SUPPORTED_BOARDS.items())

    # Main Actions 
    def compile(self, sketch_path: str) -> bool:
        """
        Přeloží sketch v zadaném adresáři pro aktuální desku.
        sketch_path: cesta ke složce se souborem .ino
        Vrací True pokud je kompilace úspěšná, jinak vyhazuje výjimku.
        """
        cli = os.path.abspath(ARDUINO_CLI_PATH)
        sketch_dir = os.path.abspath(sketch_path)
        cmd = [
            cli, "compile",
            sketch_dir,
            "-p", self.port,
            "-b", self.fqbn,
        ]
        print(f"Kompiluji: {' '.join(cmd)}")  # Ladící výpis
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Kompilace selhala: {result.stderr}")
        print(result.stdout)
        return True

    def upload(self, sketch_path: str) -> bool:
        """
        Nahraje sketch na zvolenou desku přes nastavený port (např. 'COM3' nebo '/dev/ttyUSB0').
        Vrací True pokud je nahrání úspěšné, jinak vyhazuje výjimku.
        """
        # Nejprve zkompilujeme, abychom měli jistotu, že kód je validní
        if not self.compile(sketch_path):
            raise RuntimeError("Kód nebyl úspěšně zkompilován, nahrávání se nepodařilo.")
            
        cli = os.path.abspath(ARDUINO_CLI_PATH)
        sketch_dir = os.path.abspath(sketch_path)
        cmd = [
            cli, "upload",
            sketch_dir,
            "-p", self.port,
            "-b", self.fqbn,
        ]
        print(f"Nahrávám: {' '.join(cmd)}")  # Ladící výpis
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Nahrání selhalo: {result.stderr}")
        print(result.stdout)
        return True
