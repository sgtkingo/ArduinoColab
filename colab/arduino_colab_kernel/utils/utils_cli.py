# utils_cli.py
# Robust finding of the arduino-cli executable (explicit -> env -> PATH -> package).
# No extra dependencies, cross-platform.

from __future__ import annotations
import os
import sys
import stat
import shutil
import tempfile
from pathlib import Path

# Py 3.9+: importlib.resources.files/as_file; for Py 3.8 you can use the backport 'importlib_resources'
try:
    from importlib.resources import files, as_file
except Exception:  # Py <3.9 fallback, if needed
    from importlib_resources import files, as_file  # type: ignore

# NOTE: 'tools' is a package in your bundle where the binaries are located
try:
    from arduino_colab_kernel import tools  # folder with arduino-cli in the package
except Exception:
    tools = None  # fallback if tools is not part of the package


def _is_windows() -> bool:
    """
    Checks if the current operating system is Windows.

    Returns:
        bool: True if running on Windows, False otherwise.
    """
    return os.name == "nt"


def _ensure_executable(path: Path) -> None:
    """
    On POSIX systems, sets the executable bit for the user if missing.

    Args:
        path (Path): Path to the file to make executable.

    Raises:
        Exception: If chmod fails (but is suppressed).
    """
    if _is_windows():
        return
    try:
        mode = os.stat(path).st_mode
        # add --x for user
        os.chmod(path, mode | stat.S_IXUSR)
    except Exception:
        pass


def _copy_to_temp(resource_path: Path, target_name: str | None = None) -> Path:
    """
    Copies the resource to a temp directory and returns its Path (persistent for the session).

    Args:
        resource_path (Path): Path to the resource file.
        target_name (str|None): Optional new name for the copied file.

    Returns:
        Path: Path to the copied file in the temp directory.

    Raises:
        Exception: If copying fails.
    """
    temp_dir = Path(tempfile.gettempdir()) / "arduino_colab_kernel"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dst = temp_dir / (target_name or resource_path.name)
    try:
        # if it already exists, you could compare size/mtime, but just overwrite
        shutil.copy2(str(resource_path), str(dst))
    except Exception:
        # fallback without metadata
        try:
            shutil.copy(str(resource_path), str(dst))
        except Exception as e:
            raise RuntimeError(f"Failed to copy resource to temp: {e}")
    _ensure_executable(dst)
    return dst


def resolve_arduino_cli_path(explicit_path: str | None = None) -> str:
    """
    Finds the path to the 'arduino-cli' executable:
    1) explicit path (argument) or env: ARDUINO_CLI
    2) PATH (shutil.which)
    3) resource in the package (arduino_colab_kernel.tools)
       - if it's directly on the FS, returns that
       - if it's in a zip, extracts to temp and returns the new path

    Args:
        explicit_path (str|None): Explicit path to arduino-cli, or None.

    Returns:
        str: Path to the arduino-cli executable.

    Raises:
        FileNotFoundError: If arduino-cli cannot be found by any method.
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

    # 3) resource in the package
    if tools is not None:
        try:
            resource = files(tools).joinpath(exe_name)
            # as_file ensures a real path even if the resource is in a zip
            with as_file(resource) as real_path:
                real_path = Path(real_path)
                if real_path.is_file():
                    # if it's a file in site-packages (unpacked), we can use it directly
                    # on POSIX, ensure it has the execute bit
                    _ensure_executable(real_path)
                    return str(real_path)
                # otherwise manually copy to temp (theoretically as_file already handles this)
                extracted = _copy_to_temp(real_path, exe_name)
                return str(extracted)
        except Exception as e:
            # last attempt: if files() fails, nothing is found
            pass

    raise FileNotFoundError(
        "arduino-cli was not found. Set ARDUINO_CLI, add arduino-cli to PATH, "
        "or include the binary in the package (arduino_colab_kernel/tools)."
    )
