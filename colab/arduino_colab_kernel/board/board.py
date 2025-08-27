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
    """
    Representation of HW board + serial communication via SerialPort composition.

    Attributes:
        name (str): Name of the board (e.g. "uno").
        fqbn (str): Fully Qualified Board Name for arduino-cli.
        port (str|None): Serial port device name.
        serial (SerialPort): SerialPort instance for serial communication.
    """

    def __init__(self, name: str, fqbn: str, port: str|None = None):
        """
        Initializes the Board with name, fqbn, and optional port.

        Args:
            name (str): Name of the board.
            fqbn (str): Fully Qualified Board Name.
            port (str|None): Serial port device name (optional).

        Raises:
            RuntimeError: If no port cant be suggested or set.
        """
        if not port:
            port = SerialPort.suggest_port()  # Automatically suggests port if not provided
        # Composition – serial line is separated into its own class
        self.serial = SerialPort()
        self.configure(port=port, name=name, fqbn=fqbn)

    def configure(self, **kwargs):
        """
        Updates board and serial line configuration.

        Args:
            port (str, optional): Serial port device name.
            name (str, optional): Board name.
            fqbn (str, optional): Fully Qualified Board Name.
            serial (dict, optional): Serial configuration dictionary.

        Raises:
            ValueError: If required configuration keys are missing or invalid.
            Exception: If serial configuration fails.
        """
        if "port" in kwargs:
            self.port = kwargs["port"]
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "fqbn" in kwargs:
            self.fqbn = kwargs["fqbn"]

        serial_data: dict = kwargs.get("serial", DEFAULT_SERIAL_CONFIG)
        if "port" not in serial_data:
            serial_data["port"] = self.port
        try:
            self.serial.configure(**serial_data)
        except Exception as e:
            raise RuntimeError(f"Failed to configure serial port: {e}")
        
    def export(self) -> dict:
        """
        Exports the board and serial configuration as a dictionary.

        Returns:
            dict: Dictionary containing board and serial configuration.
        """
        return {
            "name": self.name,
            "fqbn": self.fqbn,
            "port": self.port,
            "serial": self.serial.export(),
        }