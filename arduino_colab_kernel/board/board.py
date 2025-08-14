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