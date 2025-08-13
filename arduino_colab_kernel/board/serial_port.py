# serial_port.py
# Třída SerialPort: samostatná odpovědnost za sériovou komunikaci (otevřít/zavřít/číst/psát/poslouchat).
# Závislost: pyserial (pip install pyserial)

from __future__ import annotations
from typing import Optional, Iterable, Callable
import time

try:
    import serial
    from serial.tools import list_ports
except Exception as e:
    raise RuntimeError(
        "Knihovna 'pyserial' není nainstalovaná. Nainstaluj ji příkazem: pip install pyserial"
    ) from e


# ---------- Autodetekce portu ----------
def list_serial_ports() -> list[str]:
    """Vrátí seznam dostupných sériových portů (např. COM3, /dev/ttyUSB0)."""
    return [p.device for p in list_ports.comports()]

class SerialPort:
    """Zapouzdření sériového portu – konfigurace + I/O operace."""

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 0.1,
        encoding: str = "utf-8",
        autostrip: bool = True,
    ):
        # Konfigurace portu
        self.port = port                  # např. "COM5" nebo "/dev/ttyUSB0"
        self.baudrate = baudrate
        self.timeout = timeout
        self.encoding = encoding
        self.autostrip = autostrip

        # Vnitřní handle
        self._ser: Optional[serial.Serial] = None

    # ---------- Konfigurace ----------

    def configure(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        timeout: Optional[float] = None,
        encoding: Optional[str] = None,
        autostrip: Optional[bool] = None,
    ) -> None:
        """Aktualizuje konfiguraci sériového portu (bez otevření)."""
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

    # ---------- Životní cyklus ----------

    def open(self) -> None:
        """Otevře sériový port dle aktuální konfigurace."""
        if not self.port:
            raise RuntimeError("Není nastaven port. Použij SerialPort.configure(port='COMx').")
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout,
            write_timeout=self.timeout,
        )

    def close(self) -> None:
        """Bezpečně zavře sériový port."""
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        finally:
            self._ser = None

    # ---------- I/O ----------

    def readline(self) -> Optional[str]:
        """Přečte jeden řádek (neblokující dle timeoutu)."""
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
        """Přečte N řádků (neblokující smyčka – čeká v rámci timeoutů)."""
        if lines < 1:
            lines = 1
        out: list[str] = []
        while len(out) < lines:
            line = self.readline()
            if line is None:
                time.sleep(0.01)  # jemná pauza proti točení CPU
                continue
            out.append(line)
        return out

    def write(self, data: str, append_newline: bool = True) -> None:
        """Zapíše data na port (volitelně s koncovým newline)."""
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("Sériový port není otevřen. Zavolej nejprve open().")
        payload = (data + ("\n" if append_newline else "")).encode(self.encoding, errors="ignore")
        self._ser.write(payload)

    def listen(
        self,
        duration: Optional[float] = None,
        prefix: Optional[str] = None,
        printer: Callable[[str], None] = print,
    ) -> None:
        """Streamuje řádky po dobu `duration` (None = do Ctrl+C). Volitelně filtruje prefixem."""
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
        """Heuristicky vybere vhodný port (pokud je k dispozici)."""
        ports = list(list_ports.comports())
        if not ports:
            return None
        for p in ports:
            name = (p.device or "").lower()
            if "usb" in name or "acm" in name:
                return p.device
        return ports[0].device
