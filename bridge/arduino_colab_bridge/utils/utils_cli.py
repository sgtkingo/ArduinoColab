# utils_cli.py
# Robustní nalezení spustitelného arduino-cli (explicit -> env -> PATH -> balíček).
# Bez dalších závislostí, multiplatformně.

from __future__ import annotations
import os
import sys
import stat
import shutil
import tempfile
from pathlib import Path

# Py 3.9+: importlib.resources.files/as_file; pro Py 3.8 lze použít backport 'importlib_resources'
try:
    from importlib.resources import files, as_file
except Exception:  # Py <3.9 fallback, pokud by bylo potřeba
    from importlib_resources import files, as_file  # type: ignore

# POZN.: 'tools' je package v tvém balíčku, kde leží binárky
try:
    from arduino_colab_bridge import tools  # složka s arduino-cli v balíčku
except Exception:
    tools = None  # fallback, když tools není součástí balíčku


def _is_windows() -> bool:
    return os.name == "nt"


def _ensure_executable(path: Path) -> None:
    """Na POSIX nastaví executable bit, pokud chybí."""
    if _is_windows():
        return
    try:
        mode = os.stat(path).st_mode
        # přidej --x pro user
        os.chmod(path, mode | stat.S_IXUSR)
    except Exception:
        pass


def _copy_to_temp(resource_path: Path, target_name: str | None = None) -> Path:
    """Zkopíruje resource do temp adresáře a vrátí jeho Path (perzistentní po dobu sezení)."""
    temp_dir = Path(tempfile.gettempdir()) / "arduino_colab_kernel"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dst = temp_dir / (target_name or resource_path.name)
    try:
        # pokud už existuje, můžeš porovnat velikost/mtime, ale stačí přepsat
        shutil.copy2(str(resource_path), str(dst))
    except Exception:
        # fallback bez metadat
        shutil.copy(str(resource_path), str(dst))
    _ensure_executable(dst)
    return dst


def resolve_arduino_cli_path(explicit_path: str | None = None) -> str:
    """
    Najde cestu ke spustitelnému 'arduino-cli':
    1) explicitní cesta (argument) nebo env: ARDUINO_CLI
    2) PATH (shutil.which)
    3) resource v balíčku (arduino_colab_kernel.tools)
       - pokud je přímo na FS, vrátí ten
       - pokud je v zipu, rozbalí do temp a vrátí novou cestu
    Pokud nic nenalezne, vyhodí FileNotFoundError.
    """
    # 1) explicit / env
    candidate = explicit_path or os.environ.get("ARDUINO_CLI")
    if candidate:
        p = Path(candidate)
        if p.is_file():
            return str(p)

    # 2) PATH
    exe_name = "arduino-cli.exe" if _is_windows() else "arduino-cli"
    found = shutil.which(exe_name)
    if found:
        return found

    # 3) resource v balíčku
    if tools is not None:
        try:
            resource = files(tools).joinpath(exe_name)
            # as_file zajistí skutečnou cestu i pokud je resource v zipu
            with as_file(resource) as real_path:
                real_path = Path(real_path)
                if real_path.is_file():
                    # pokud je to soubor v site-packages (rozbalený), můžeme ho použít přímo
                    # na POSIX se ujistíme, že má execute bit
                    _ensure_executable(real_path)
                    return str(real_path)
                # jinak ručně zkopíruj do temp (teoreticky už to as_file řeší)
                extracted = _copy_to_temp(real_path, exe_name)
                return str(extracted)
        except Exception:
            # poslední pokus: pokud by files() selhaly, nic nenajdeme
            pass

    raise FileNotFoundError(
        "arduino-cli nebyl nalezen. Nastav ARDUINO_CLI, přidej arduino-cli do PATH, "
        "nebo zahrň binárku do balíčku (arduino_colab_kernel/tools)."
    )
