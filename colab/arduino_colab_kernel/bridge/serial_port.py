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
    """Returns a list of available serial ports (e.g. COM3, /dev/ttyUSB0)."""
    return [p.device for p in list_ports.comports()]

class SerialPort:
    """Encapsulation of a serial port – configuration + I/O operations."""

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 0.1,
        encoding: str = "utf-8",
        autostrip: bool = True,
    ):
        # Port configuration
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
        """Updates serial port configuration (without opening)."""
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
        """Opens the serial port according to the current configuration."""
        if not self.port:
            raise RuntimeError("Port is not set. Use SerialPort.configure(port='COMx').")
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout,
            write_timeout=self.timeout,
        )

    def close(self) -> None:
        """Safely closes the serial port."""
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        finally:
            self._ser = None

    # ---------- I/O ----------

    def readline(self) -> Optional[str]:
        """Reads one line (non-blocking according to timeout)."""
        if not self._ser or not self._ser.is_open:
            return None
        raw = self._ser.readline()
        if not raw:
            return None
        try:
            txt = raw.decode(self.encoding, errors="replace")
        except Exception:
            txt = raw.decode("latin-1", errors="replace")
        return txt.rstrip("\r\n") if self.autostrip else txt

    def read(self, lines: int = 1) -> list[str]:
        """Reads N lines (non-blocking loop – waits within timeouts)."""
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
        """Writes data to the port (optionally with trailing newline)."""
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("Serial port is not open. Call open() first.")
        payload = (data + ("\n" if append_newline else "")).encode(self.encoding, errors="ignore")
        self._ser.write(payload)

    def listen(
        self,
        duration: Optional[float] = None,
        prefix: Optional[str] = None,
        printer: Callable[[str], None] = print,
    ) -> None:
        """Streams lines for `duration` seconds (None = until Ctrl+C). Optionally filters by prefix."""
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

    # ---------- Utility ----------

    @staticmethod
    def suggest_port() -> Optional[str]:
        """Heuristically selects a suitable port (if available)."""
        ports = list(list_ports.comports())
        if not ports:
            return None
        for p in ports:
            name = (p.device or "").lower()
            if "usb" in name or "acm" in name:
                return p.device
        return ports[0].device
