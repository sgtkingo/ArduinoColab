# serial_port.py
# SerialPort class: separate responsibility for serial communication (open/close/read/write/listen).
# Dependency: pyserial (pip install pyserial)

from __future__ import annotations
from typing import Optional, Iterable, Callable
import time

try:
    import serial
    from serial.tools import list_ports
except Exception as e:
    raise RuntimeError(
        "The 'pyserial' library is not installed. Install it with: pip install pyserial"
    ) from e


# ---------- Port autodetection ----------
def list_serial_ports() -> list[str]:
    """
    Returns a list of available serial ports (e.g. COM3, /dev/ttyUSB0).

    Returns:
        list[str]: List of serial port device names.
    """
    return [p.device for p in list_ports.comports()]

class SerialPort:
    """
    Encapsulation of a serial port – configuration + I/O operations.

    Attributes:
        port (Optional[str]): Serial port device name.
        baudrate (int): Baud rate for communication.
        timeout (float): Read/write timeout in seconds.
        encoding (str): Encoding for text I/O.
        autostrip (bool): Whether to strip line endings on read.
        _ser (Optional[serial.Serial]): Internal pyserial handle.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 0.1,
        encoding: str = "utf-8",
        autostrip: bool = True,
    ):
        """
        Initializes the SerialPort with configuration.

        Args:
            port (Optional[str]): Serial port device name.
            baudrate (int): Baud rate for communication.
            timeout (float): Read/write timeout in seconds.
            encoding (str): Encoding for text I/O.
            autostrip (bool): Whether to strip line endings on read.

        Raises:
            RuntimeError: If no port is available.
        """
        if not port:
            port = SerialPort.suggest_port()
        self.port = port                  # e.g. "COM5" or "/dev/ttyUSB0"
        self.baudrate = baudrate
        self.timeout = timeout
        self.encoding = encoding
        self.autostrip = autostrip

        # Internal handle
        self._ser: Optional[serial.Serial] = None

    # ---------- Configuration ----------

    def configure(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        timeout: Optional[float] = None,
        encoding: Optional[str] = None,
        autostrip: Optional[bool] = None,
    ) -> None:
        """
        Updates serial port configuration (without opening).

        Args:
            port (Optional[str]): Serial port device name.
            baudrate (Optional[int]): Baud rate.
            timeout (Optional[float]): Timeout in seconds.
            encoding (Optional[str]): Encoding for text I/O.
            autostrip (Optional[bool]): Whether to strip line endings on read.
        """
        if port is not None:
            self.port = port
        if baudrate is not None:
            self.baudrate = baudrate
        if timeout is not None:
            self.timeout = timeout
        if encoding is not None:
            self.encoding = encoding
        if autostrip is not None:
            self.autostrip = autostrip

    # ---------- Lifecycle ----------

    def open(self) -> None:
        """
        Opens the serial port according to the current configuration.

        Raises:
            RuntimeError: If port is not set or opening fails.
        """
        if not self.port:
            raise RuntimeError("Port is not set. Use SerialPort.configure(port='COMx').")
        if self._ser and self._ser.is_open:
            return
        try:
            self._ser = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to open serial port '{self.port}': {e}")

    def close(self) -> None:
        """
        Safely closes the serial port.

        Raises:
            Exception: If closing the port fails.
        """
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception as e:
            raise RuntimeError(f"Failed to close serial port: {e}")
        finally:
            self._ser = None

    # ---------- I/O ----------

    def readline(self) -> Optional[str]:
        """
        Reads one line (non-blocking according to timeout).

        Returns:
            Optional[str]: The line read, or None if nothing is read.

        Raises:
            Exception: If reading from serial fails.
        """
        if not self._ser or not self._ser.is_open:
            return None
        try:
            raw = self._ser.readline()
        except Exception as e:
            raise RuntimeError(f"Failed to read line from serial port: {e}")
        if not raw:
            return None
        try:
            txt = raw.decode(self.encoding, errors="replace")
        except Exception:
            txt = raw.decode("latin-1", errors="replace")
        return txt.rstrip("\r\n") if self.autostrip else txt

    def read(self, lines: int = 1) -> list[str]:
        """
        Reads N lines (non-blocking loop – waits within timeouts).

        Args:
            lines (int): Number of lines to read.

        Returns:
            list[str]: List of lines read.

        Raises:
            Exception: If reading from serial fails.
        """
        if lines < 1:
            lines = 1
        out: list[str] = []
        while len(out) < lines:
            line = self.readline()
            if line is None:
                time.sleep(0.01)  # gentle pause to avoid CPU spinning
                continue
            out.append(line)
        return out

    def write(self, data: str, append_newline: bool = True) -> None:
        """
        Writes data to the port (optionally with trailing newline).

        Args:
            data (str): Data to write.
            append_newline (bool): Whether to append a newline.

        Raises:
            RuntimeError: If serial port is not open or writing fails.
        """
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("Serial port is not open. Call open() first.")
        try:
            payload = (data + ("\n" if append_newline else "")).encode(self.encoding, errors="ignore")
            self._ser.write(payload)
        except Exception as e:
            raise RuntimeError(f"Failed to write to serial port: {e}")

    def listen(
        self,
        duration: Optional[float] = None,
        prefix: Optional[str] = None,
        printer: Callable[[str], None] = print,
    ) -> None:
        """
        Streams lines for `duration` seconds (None = until Ctrl+C). Optionally filters by prefix.

        Args:
            duration (Optional[float]): Duration in seconds to listen, or None for unlimited.
            prefix (Optional[str]): Only print lines starting with this prefix.
            printer (Callable[[str], None]): Function to call for each line.

        Raises:
            Exception: If reading from serial fails.
        """
        start = time.time()
        try:
            while True:
                if duration is not None and (time.time() - start) >= duration:
                    break
                line = self.readline()
                if line is None:
                    continue
                if prefix is not None and not line.startswith(prefix):
                    continue
                printer(line)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            raise RuntimeError(f"Error during serial listen: {e}")

    # ---------- Utility ----------

    @staticmethod
    def suggest_port() -> Optional[str]:
        """
        Heuristically selects a suitable port (if available).

        Returns:
            Optional[str]: Device name of a suitable port, or None if none found.
        """
        ports = list(list_ports.comports())
        if not ports:
            return None
        for p in ports:
            name = (p.device or "").lower()
            if "usb" in name or "acm" in name:
                return p.device
        return ports[0].device
