# board_manager.py
# Správa výběru a nahrávání na podporované Arduino desky (Uno, Nano)
# Požaduje instalaci arduino-cli a příslušného toolchainu.

from __future__ import annotations
import subprocess
import os
from typing import Optional
from arduino_colab_kernel.board.serial_port import SerialPort

# board.py
# Třída Board: drží konfiguraci cílové desky (name, fqbn) a kompozici SerialPortu.
# Board samotný neřeší build/upload (to řeší BoardManager), pouze sériové I/O deleguje na SerialPort.
DEFAULT_SERIAL_CONFIG = {
    "baudrate": 115200,
    "timeout": 0.1,
    "encoding": "utf-8",
    "autostrip": True,
}

class Board:
    """Reprezentace HW desky + sériová komunikace přes kompozici SerialPortu."""

    def __init__(self, name: str, fqbn: str, port: str|None = None):
        # Identita desky
        self.name = name      # např. "uno", "nano"
        self.fqbn = fqbn      # např. "arduino:avr:uno"
        if not port:
            port = SerialPort.suggest_port()  # Automaticky navrhne port, pokud není zadán
        self.port = port      # např. "COM5" nebo "/dev/ttyUSB0"

        # Kompozice – sériová linka je vyčleněná do samostatné třídy
        self.serial = SerialPort()
        self.serial.configure(port=port, **DEFAULT_SERIAL_CONFIG)  #default konfigurace

    def configure(self, **kwargs):
        """Aktualizuje konfiguraci boardu a sériové linky."""
        if "port" in kwargs:
            self.port = kwargs["port"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "fqbn" in kwargs:
            self.fqbn = kwargs["fqbn"]
            
        self.serial.configure(**kwargs)

# board_manager.py
# Správa výběru desky + build/upload přes arduino-cli. Sériové I/O je v kompozici: Board.serial.
import os
import subprocess
from typing import Optional, Tuple, Dict

ARDUINO_CLI_PATH = r"./tools/arduino-cli.exe"  # Cesta k arduino-cli, pokud není v PATH

SUPPORTED_BOARDS = {
    "uno":  "arduino:avr:uno",
    "nano": "arduino:avr:nano",
}

def _append_log(log_file: str, cmd: list[str], stdout: str, stderr: str, ok: bool):
    """Zapíše log kompilace/nahrávání do souboru."""
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

    # ---------- Výběr desky ----------
    def list_boards(self) -> Dict[str, str]:
        """
        Vrací seznam podporovaných desek jako seznam dvojic (jméno, FQBN).
        """
        return SUPPORTED_BOARDS

    def select_board(self, name: str):
        key = name.strip().lower()
        if key not in SUPPORTED_BOARDS:
            raise ValueError(f"Deska '{name}' není podporována. Podporované: {list(SUPPORTED_BOARDS.keys())}")
        self.board = Board(name=key, fqbn=SUPPORTED_BOARDS[key])

    def require_board(self) -> Board:
        if not self.board:
            raise RuntimeError("Není nastavena žádná deska. Zavolej set_board('uno'|'nano').")
        return self.board

    # ---------- Sériová konfigurace ----------

    def configure(self, **kwargs):
        self.require_board().configure(**kwargs)

    # ---------- Build & upload ----------

    def _cli(self) -> str:
        if not os.path.exists(ARDUINO_CLI_PATH):
            raise FileNotFoundError(f"arduino-cli nenalezeno: {ARDUINO_CLI_PATH}")
        return ARDUINO_CLI_PATH
    
    def compile(self, sketch_path: str, log_file: Optional[str] = None) -> bool:
        """
        Přeloží sketch v zadaném adresáři pro aktuální desku.
        sketch_path: cesta ke složce se souborem .ino
        Vrací True pokud je kompilace úspěšná, jinak vyhazuje výjimku.
        """
        
        b = self.require_board()
        cli = os.path.abspath(ARDUINO_CLI_PATH)
        sketch_dir = os.path.abspath(sketch_path)
        cmd = [
            cli, "compile",
            sketch_dir,
            "-p", b.port,
            "-b", b.fqbn,
        ]
        print(f"Kompiluji: {' '.join(cmd)}")  # Ladící výpis
        result = subprocess.run(cmd, capture_output=True, text=True)
        ok = (result.returncode == 0)
        if not ok:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Nahrání selhalo: {result.stderr}")
        print(result.stdout)
        
        if log_file:
            _append_log(log_file, cmd, result.stdout, result.stderr, ok)
            
        return ok

    def upload(self, sketch_path: str, log_file: Optional[str] = None) -> bool:
        """
        Nahraje sketch na zvolenou desku přes nastavený port (např. 'COM3' nebo '/dev/ttyUSB0').
        Vrací True pokud je nahrání úspěšné, jinak vyhazuje výjimku.
        """
        # Nejprve zkompilujeme, abychom měli jistotu, že kód je validní
        if not self.compile(sketch_path):
            raise RuntimeError("Kód nebyl úspěšně zkompilován, nahrávání se nepodařilo.")
        
        b = self.require_board()
        cli = os.path.abspath(ARDUINO_CLI_PATH)
        sketch_dir = os.path.abspath(sketch_path)
        cmd = [
            cli, "upload",
            sketch_dir,
            "-p", b.port,
            "-b", b.fqbn,
        ]
        print(f"Nahrávám: {' '.join(cmd)}")  # Ladící výpis
        result = subprocess.run(cmd, capture_output=True, text=True)
        ok = (result.returncode == 0)
        if not ok:
            print(result.stdout)
            print(result.stderr)
            raise RuntimeError(f"Nahrání selhalo: {result.stderr}")
        print(result.stdout)
        
        if log_file:
            _append_log(log_file, cmd, result.stdout, result.stderr, ok)
            
        return ok
    
    def export(self) -> dict:
        # Vrací konfiguraci aktuální desky a sériového portu jako slovík
        b = self.require_board()
        if not b:
            raise RuntimeError("Není nastavena žádná deska.")
        return {
            "name": b.name,
            "fqbn": b.fqbn,
            "port": b.port,
            "baudrate": b.serial.baudrate,
            "timeout": b.serial.timeout,
            "encoding": b.serial.encoding,
            "autostrip": b.serial.autostrip
        } 

# Singleton for magics
board_manager = BoardManager()