from arduino_colab_kernel.bridge.serial_port import SerialPort
# board.py
# Board class: holds configuration of the target board (name, fqbn) and composition of SerialPort.
# Board itself does not handle build/upload (that is handled by BoardManager), only delegates serial I/O to SerialPort.
DEFAULT_SERIAL_CONFIG = {
    "baudrate": 115200,
    "timeout": 0.1,
    "encoding": "utf-8",
    "autostrip": True,
}

class Board:
    """Representation of HW board + serial communication via SerialPort composition."""

    def __init__(self, name: str, fqbn: str, port: str|None = None):
        if not port:
            port = SerialPort.suggest_port()  # Automatically suggests port if not provided

        # Composition – serial line is separated into its own class
        self.serial = SerialPort()
        self.configure(port=port, name=name, fqbn=fqbn)

    def configure(self, **kwargs):
        """Updates board and serial line configuration."""
        if "port" in kwargs:
            self.port = kwargs["port"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "fqbn" in kwargs:
            self.fqbn = kwargs["fqbn"]
            
        serial_data:dict = kwargs.get("serial", DEFAULT_SERIAL_CONFIG)
        self.serial.configure(port=self.port, **serial_data)