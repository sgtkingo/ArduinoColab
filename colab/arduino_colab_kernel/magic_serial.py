# magic_serial.py
# Magická buňka %%serial pro práci se sériovou linkou.

import shlex
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import Markdown, display
from arduino_colab_kernel.board.board_manager import board_manager  # globální instance Boardboard_manager

def _help() -> str:
    """Vrací nápovědu pro %%serial."""
    return (
        "**Použití:** `%%serial [listen|read|write|help] [options]`\n\n"
        "**Příkazy:**\n"
        "- `listen` – čte sériový výstup kontinuálně po dobu `--duration` nebo do přerušení (Ctrl+C)\n"
        "- `read` – přečte zadaný počet řádků (`--lines`)\n"
        "- `write` – zapíše data na sériový port (`--data` nebo obsah buňky)\n"
        "- `help` – zobrazí tuto nápovědu\n\n"
        "**Společné požadavky:**\n"
        "- Musí být nastavena deska (`%board set`) a sériový port (`%board serial` nebo autodetekce)\n\n"
        "**Options pro `listen`:**\n"
        "- `--duration <sekundy>` – délka poslechu; pokud není uvedeno, běží do Ctrl+C\n"
        "- `--prefix <text>` – filtruje řádky začínající daným prefixem\n\n"
        "**Options pro `read`:**\n"
        "- `--lines <počet>` – počet řádků k přečtení (výchozí 1)\n\n"
        "**Options pro `write`:**\n"
        "- `--data <text>` – text k odeslání; pokud není uvedeno, použije se obsah buňky\n"
        "- `--no-nl` – neposílat na konec zprávy znak nového řádku (`\\n`)\n"
    )

def _parse_serial_args(line: str):
    """Rozparsuje argumenty pro listen/read/write."""
    args = shlex.split(line)
    if not args:
        return "", {}
    cmd = args[0].lower()
    opts = {
        "duration": None,
        "prefix": None,
        "lines": 1,
        "data": None,
        "no_nl": False
    }
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--duration":
            i += 1; opts["duration"] = float(args[i])
        elif a == "--prefix":
            i += 1; opts["prefix"] = args[i]
        elif a == "--lines":
            i += 1; opts["lines"] = int(args[i])
        elif a == "--data":
            i += 1; opts["data"] = args[i]
        elif a == "--no-nl":
            opts["no_nl"] = True
        else:
            display(Markdown(f"**Neznámý argument:** `{a}`"))
        i += 1
    return cmd, opts


@magics_class
class SerialMagic(Magics):

    @line_magic
    def serial(self, line, cell=None):
        """Magická buňka %%serial pro práci se sériovým portem."""
        cmd, opts = _parse_serial_args(line)

        if cmd == "help" or cmd == "":
            display(Markdown(_help()))
            return

        if cmd not in ("listen", "read", "write"):
            display(Markdown("**Neznámý příkaz.**\n\n" + _help()))
            return

        try:
            board = board_manager.require_board()
            sp = board.serial
            sp.open()

            if cmd == "listen":
                duration = opts["duration"]
                prefix = opts["prefix"]
                display(Markdown(
                    f"📡 **Listening** – port: `{sp.port}`, baud: `{sp.baudrate}`"
                    + (f", doba: {duration}s" if duration else ", doba: neomezeně")
                    + (f", filtr prefix: `{prefix}`" if prefix else "")
                ))
                sp.listen(duration=duration, prefix=prefix, printer=print)
                display(Markdown("✅ **Konec poslechu.**"))

            elif cmd == "read":
                lines = max(1, opts["lines"])
                for ln in sp.read(lines=lines):
                    print(ln)

            elif cmd == "write":
                payload = opts["data"] if opts["data"] is not None else (cell or "")
                sp.write(payload, append_newline=not opts["no_nl"])
                display(Markdown(f"✉️ **Odesláno:** `{payload.strip()}`"))

        except Exception as e:
            display(Markdown(f"**Chyba:** `{e}`"))
        finally:
            try:
                sp.close()
            except Exception:
                pass


def load_ipython_extension(ipython):
    ipython.register_magics(SerialMagic)
