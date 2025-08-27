# magic_board.py
# Line magic %board – board selection, serial port, build/upload and utilities (with port autodetection and logging).

import os
import shlex
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.board.board_manager import board_manager
from arduino_colab_kernel.project.project_manager import project_manager
from arduino_colab_kernel.bridge.bridge import bridge_manager
from arduino_colab_kernel.bridge.serial_port import list_serial_ports

def _help() -> str:
    """
    Returns help text for the %board magic command.

    Returns:
        str: Markdown-formatted help text.
    """
    text = """
### 🔧 Available `%board` commands

| Command                          | Parameters                                                     | Description                                                           |
|-----------------------------------|---------------------------------------------------------------|-----------------------------------------------------------------------|
| **`%board select`**               | `[uno\|nano]`                                                 | Selects a supported board (if port is not set, tries autodetection).  |
| **`%board status`**               | *(no parameters)*                                             | Shows current settings (board, FQBN, serial port).                    |
| **`%board serial`**               | `[--port COMx] [--baud 115200] [--timeout 0.1] [--encoding utf-8] [--strip true\|false]` | Sets serial port and its parameters.                                  |
| **`%board compile`**              | `[sketch_dir_or_ino] [--log-file path]`*(optional)*           | Compiles sketch for the currently selected board.                     |
| **`%board upload`**               | `[sketch_dir_or_ino] [--log-file path]`*(optional)*           | Uploads sketch to the currently selected board.                       |
| **`%board list`**                 | *(no parameters)*                                             | Lists available supported boards.                                     |
| **`%board ports`**                | *(no parameters)*                                             | Lists available serial ports.                                         |
| **`%board help`** / **`?`**       | *(no parameters)*                                             | Shows this help.                                                      |
    """
    return text

def _parse_select_args(args: list[str]) -> tuple[str|None, dict]:
    """
    Parses arguments for '%board select'.

    Args:
        args (list[str]): List of arguments.

    Returns:
        tuple[str|None, dict]: (board_name, serial_cfg_dict), where serial_cfg_dict contains only 'port' (if specified).
    """
    if not args:
        return None, {}
    name = args[0].lower()
    cfg = {}
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--port":
            i += 1; cfg["port"] = args[i]
        else:
            display(Markdown(f"**Unknown argument for `set`:** `{a}`"))
        i += 1
    return name, cfg

def _parse_serial_args(args: list[str]) -> dict:
    """
    Parses arguments for '%board serial'.

    Args:
        args (list[str]): List of arguments.

    Returns:
        dict: Serial configuration dictionary.
    """
    cfg = {"port": None, "baudrate": None, "timeout": None, "encoding": None, "autostrip": None}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--port":
            i += 1; cfg["port"] = args[i]
        elif a == "--baud":
            i += 1; cfg["baudrate"] = int(args[i])
        elif a == "--timeout":
            i += 1; cfg["timeout"] = float(args[i])
        elif a == "--encoding":
            i += 1; cfg["encoding"] = args[i]
        elif a in ("--strip", "--autostrip"):
            i += 1; cfg["autostrip"] = args[i].lower() in ("1", "true", "yes", "y")
        else:
            display(Markdown(f"**Unknown argument for `serial`:** `{a}`"))
        i += 1
    return {k: v for k, v in cfg.items() if v is not None}

def _parse_logfile(args: list[str]) -> tuple[list[str], str | None]:
    """
    Parses log file argument from a list of arguments.

    Args:
        args (list[str]): List of arguments.

    Returns:
        tuple[list[str], str|None]: (args_without_log, log_file|None)
    """
    out = []
    log_file = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--log-file":
            if i + 1 >= len(args):
                display(Markdown("**Missing value for `--log-file`.**"))
                return args, None
            log_file = args[i + 1]
            i += 2
            continue
        out.append(a)
        i += 1
    return out, log_file

@magics_class
class BoardMagic(Magics):
    """
    Implements the %board magic command for board selection, configuration, and utilities.
    """

    @line_magic
    def board(self, line: str = ""):
        """
        Handles the %board magic command.

        Args:
            line (str): The command line input after %board.

        Raises:
            Displays errors as Markdown output, does not raise.
        """
        args = shlex.split(line)
        if not args:
            display(Markdown(_help()))
            return

        cmd = args[0].lower()
        rest = args[1:]

        try:
            if cmd == "help" or cmd == "?":
                display(Markdown(_help()))
                return

            if cmd == "list":
                try:
                    boards = board_manager.list_boards().items()
                    if boards:
                        display(Markdown("**Available boards:**  \n" + "\n".join(f"- `{name}` (FQBN: `{fqbn}`)" for name, fqbn in boards)))
                    else:
                        display(Markdown("**No supported board found.**"))
                except Exception as e:
                    display(Markdown(f"**Error listing boards:** `{e}`"))
                return

            if cmd == "select":
                try:
                    name, cfg = _parse_select_args(rest)
                    if not name:
                        display(Markdown("**Usage:** `%board select [uno|nano] [--port COMx]`"))
                        return

                    # Set board
                    board_manager.select_board(name)
                    b = board_manager.require_board()

                    # Set board configuration
                    b.configure(**cfg)

                    # Port – either explicitly set or autodetected
                    if "port" in cfg:
                        display(Markdown(
                            f"✅ Board **{b.name}** set (FQBN `{b.fqbn}`) &nbsp;|&nbsp; Port: `{cfg['port']}` (explicit)"
                        ))
                    else:
                        if b.port:
                            display(Markdown(
                                f"✅ Board **{b.name}** set (FQBN `{b.fqbn}`) &nbsp;|&nbsp; Auto port: `{b.port}`"
                            ))
                        else:
                            display(Markdown(
                                f"✅ Board **{b.name}** set (FQBN `{b.fqbn}`) &nbsp;|&nbsp; "
                                "_Port n/a – set `%board serial --port COMx`_"
                            ))
                except Exception as e:
                    display(Markdown(f"**Error selecting board:** `{e}`"))
                return

            if cmd == "status":
                try:
                    b = board_manager.require_board()
                    sp = b.serial
                    display(Markdown(
                        f"**Board status**\n\n"
                        f"- Board: `{b.name}`\n"
                        f"- FQBN: `{b.fqbn}`\n"
                        f"- Port: `{sp.port or 'not set'}`\n"
                        f"- Baud: `{sp.baudrate}`\n"
                        f"- Timeout: `{sp.timeout}`\n"
                        f"- Encoding: `{sp.encoding}`\n"
                        f"- Auto strip: `{sp.autostrip}`\n"
                    ))
                except Exception as e:
                    display(Markdown(f"**Error showing status:** `{e}`"))
                return

            if cmd == "serial":
                try:
                    b = board_manager.require_board()
                    kv = _parse_serial_args(rest)
                    if not kv:
                        display(Markdown(
                            "**Usage:** `%board serial --port COMx [--baud 115200] [--timeout 0.1] "
                            "[--encoding utf-8] [--strip true|false]`"
                        ))
                        return
                    b.configure(**kv)
                    sp = b.serial
                    display(Markdown(
                        f"🔧 Serial configuration: port=`{sp.port}` baud=`{sp.baudrate}` "
                        f"timeout=`{sp.timeout}` enc=`{sp.encoding}` strip=`{sp.autostrip}`"
                    ))
                except Exception as e:
                    display(Markdown(f"**Error configuring serial:** `{e}`"))
                return

            if cmd == "compile":
                try:
                    log_file = os.path.join(project_manager.get_logs_dir(as_abs=False), "compile.log")
                    if rest:
                        rest, log_file = _parse_logfile(rest)
                        
                    b = board_manager.require_board()
                    sketch_file = project_manager.save(get_sketch=True)
                    ok = bridge_manager.compile(board=b, sketch_source=sketch_file, log_file=log_file)
                    if ok:
                        msg = "✅ **Compilation successful.**"
                        if log_file:
                            msg += f" Log: `{os.path.abspath(log_file)}`"
                        display(Markdown(msg))
                except Exception as e:
                    display(Markdown(f"**Error during compilation:** `{e}`"))
                return

            if cmd == "upload":
                try:
                    log_file = os.path.join(project_manager.get_logs_dir(as_abs=False), "upload.log")
                    if rest:
                        rest, log_file = _parse_logfile(rest)
                    
                    b = board_manager.require_board()
                    sketch_file = project_manager.save(get_sketch=True)
                    ok = bridge_manager.upload(board=b, sketch_source=sketch_file, log_file=log_file)
                    if ok:
                        msg = "🚀 **Upload complete.**"
                        if log_file:
                            msg += f" Log: `{os.path.abspath(log_file)}`"
                        display(Markdown(msg))
                except Exception as e:
                    display(Markdown(f"**Error during upload:** `{e}`"))
                return

            if cmd == "ports":
                try:
                    ports = list_serial_ports()
                    if ports:
                        display(Markdown("**Available serial ports:**  \n" + "\n".join(f"- `{p}`" for p in ports)))
                    else:
                        display(Markdown("**No serial port found.**"))
                except Exception as e:
                    display(Markdown(f"**Error listing ports:** `{e}`"))
                return

            display(Markdown(f"**Unknown command:** `{cmd}`\n\n" + _help()))

        except Exception as e:
            display(Markdown(f"**Error:** `{e}`"))

def load_ipython_extension(ipython):
    """
    Registers the BoardMagic class as an IPython extension.

    Args:
        ipython: The IPython interactive shell instance.
    """
    ipython.register_magics(BoardMagic)
