# magic_board.py
# Line magic %board – nastavení desky, sériové linky, build/upload a utility (s autodetekcí portu a logováním).

import os
import shlex
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.board.board_manager import board_manager
from arduino_colab_kernel.project.project_manager import project_manager
from arduino_colab_kernel.board.serial_port import list_serial_ports

def _help():
    return (
        "**%board – příkazy**\n\n"
        "- `%board select [uno|nano]` – vybere podporovanou desku (pokud není nastaven port, zkusí se autodetekce)\n"
        "- `%board status` – vypíše aktuální nastavení (deska, FQBN, sériový port)\n"
        "- `%board serial [--port COMx] [--baud 115200] [--timeout 0.1] [--encoding utf-8] [--strip true|false]` – nastaví sériový port\n"
        "- `%board compile [sketch_dir_or_ino] [--log-file path]` – přeloží sketch\n"
        "- `%board upload  [sketch_dir_or_ino] [--log-file path]` – nahraje sketch\n"
        "- `%board list` - vypíše dostupné podporované desky\n"
        "- `%board ports` – vypíše dostupné sériové porty\n"
        "- `%board help|?` – nápověda\n"
    )

def _parse_select_args(args: list[str]) -> tuple[str|None, dict]:
    """
    Parsuje argumenty pro '%board select'.
    Vrací (board_name, serial_cfg_dict), kde serial_cfg_dict obsahuje pouze 'port' (pokud je zadaný).
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
            display(Markdown(f"**Neznámý argument pro `set`:** `{a}`"))
        i += 1
    return name, cfg


def _parse_serial_args(args: list[str]) -> dict:
    cfg = {"port": None|str, "baudrate": None|str, "timeout": None|str, "encoding": None|str, "autostrip": None|str}
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
            display(Markdown(f"**Neznámý argument pro `serial`:** `{a}`"))
        i += 1
    return {k: v for k, v in cfg.items() if v is not None}


def _parse_logfile(args: list[str]) -> tuple[list[str], str | None]:
    """Vrátí (args_bez_log, log_file|None)."""
    out = []
    log_file = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--log-file":
            if i + 1 >= len(args):
                display(Markdown("**Chybí hodnota pro `--log-file`.**"))
                return args, None
            log_file = args[i + 1]
            i += 2
            continue
        out.append(a)
        i += 1
    return out, log_file


@magics_class
class BoardMagic(Magics):

    @line_magic
    def board(self, line: str = ""):
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
                boards = board_manager.list_boards().items()
                if boards:
                    display(Markdown("**Dostupné desky:**  \n" + "\n".join(f"- `{name}` (FQBN: `{fqbn}`)" for name,fqbn in boards)))
                else:
                    display(Markdown("**Nebyla nalezena žádná podporovaná deska.**"))
                return
            if cmd == "select":
                name, cfg = _parse_select_args(rest)
                if not name:
                    display(Markdown("**Použití:** `%board select [uno|nano] [--port COMx]`"))
                    return

                # Nastavení desky
                board_manager.select_board(name)
                b = board_manager.require_board()

                # Nastavení konfigurace desky
                b.configure(**cfg)

                # Port – buď explicitně zadaný, nebo autodetekce
                if "port" in cfg:
                    display(Markdown(
                        f"✅ Nastavena deska **{b.name}** (FQBN `{b.fqbn}`) &nbsp;|&nbsp; Port: `{cfg['port']}` (explicitní)"
                    ))
                else:
                    if b.port:
                        display(Markdown(
                            f"✅ Nastavena deska **{b.name}** (FQBN `{b.fqbn}`) &nbsp;|&nbsp; Auto port: `{b.port}`"
                        ))
                    else:
                        display(Markdown(
                            f"✅ Nastavena deska **{b.name}** (FQBN `{b.fqbn}`) &nbsp;|&nbsp; "
                            "_Port n/d – nastav `%board serial --port COMx`_"
                        ))
                return

            if cmd == "status":
                b = board_manager.require_board()
                sp = b.serial
                display(Markdown(
                    f"**Board status**\n\n"
                    f"- Deska: `{b.name}`\n"
                    f"- FQBN: `{b.fqbn}`\n"
                    f"- Port: `{sp.port or 'nenastaveno'}`\n"
                    f"- Baud: `{sp.baudrate}`\n"
                    f"- Timeout: `{sp.timeout}`\n"
                    f"- Encoding: `{sp.encoding}`\n"
                    f"- Auto strip: `{sp.autostrip}`\n"
                ))
                return

            if cmd == "serial":
                b = board_manager.require_board()
                kv = _parse_serial_args(rest)
                if not kv:
                    display(Markdown(
                        "**Použití:** `%board serial --port COMx [--baud 115200] [--timeout 0.1] "
                        "[--encoding utf-8] [--strip true|false]`"
                    ))
                    return
                b.configure(**kv)
                sp = b.serial
                display(Markdown(
                    f"🔧 Sériová konfigurace: port=`{sp.port}` baud=`{sp.baudrate}` "
                    f"timeout=`{sp.timeout}` enc=`{sp.encoding}` strip=`{sp.autostrip}`"
                ))
                return

            if cmd == "compile":
                if not rest:
                    display(Markdown("**Použití:** `%board compile [--log-file path]`"))
                    return
                # extrahuj --log-file, zbytek je sketch
                rest, log_file = _parse_logfile(rest)
                sketch_file = project_manager.save()
                ok = board_manager.compile(sketch_file, log_file=log_file)
                if ok:
                    msg = "✅ **Kompilace úspěšná.**"
                    if log_file:
                        msg += f" Log: `{os.path.abspath(log_file)}`"
                    display(Markdown(msg))
                return

            if cmd == "upload":
                if not rest:
                    display(Markdown("**Použití:** `%board upload [--log-file path]`"))
                    return
                rest, log_file = _parse_logfile(rest)
                sketch_file = project_manager.save()
                ok = board_manager.upload(sketch_file, log_file=log_file)
                if ok:
                    msg = "🚀 **Nahrávání dokončeno.**"
                    if log_file:
                        msg += f" Log: `{os.path.abspath(log_file)}`"
                    display(Markdown(msg))
                return

            if cmd == "ports":
                ports = list_serial_ports()
                if ports:
                    display(Markdown("**Dostupné sériové porty:**  \n" + "\n".join(f"- `{p}`" for p in ports)))
                else:
                    display(Markdown("**Nebyl nalezen žádný sériový port.**"))
                return

            display(Markdown(f"**Neznámý příkaz:** `{cmd}`\n\n" + _help()))

        except Exception as e:
            display(Markdown(f"**Chyba:** `{e}`"))


def load_ipython_extension(ipython):
    ipython.register_magics(BoardMagic)
