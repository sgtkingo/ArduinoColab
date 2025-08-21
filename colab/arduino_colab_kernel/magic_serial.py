# magic_serial.py
# Magic cell %%serial for working with the serial port.

import shlex
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import Markdown, display
from arduino_colab_kernel.bridge.bridge import bridge_manager  # Use bridge_manager instead of direct board access

def _help() -> str:
    """Returns help for %%serial."""
    return (
        "**Usage:** `%%serial [listen|read|write|help] [options]`\n\n"
        "**Commands:**\n"
        "- `listen` – reads serial output continuously for `--duration` or until interrupted (Ctrl+C)\n"
        "- `read` – reads the specified number of lines (`--lines`)\n"
        "- `write` – writes data to the serial port (`--data` or cell content)\n"
        "- `help` – shows this help\n\n"
        "**Common requirements:**\n"
        "- Board must be set (`%board set`) and serial port (`%board serial` or autodetect)\n\n"
        "**Options for `listen`:**\n"
        "- `--duration <seconds>` – listening duration; if not set, runs until Ctrl+C\n"
        "- `--prefix <text>` – filters lines starting with the given prefix\n\n"
        "**Options for `read`:**\n"
        "- `--lines <count>` – number of lines to read (default 1)\n\n"
        "**Options for `write`:**\n"
        "- `--data <text>` – text to send; if not set, uses cell content\n"
        "- `--no-nl` – do not send newline (`\\n`) at the end of the message\n"
    )

def _parse_serial_args(line: str):
    """Parses arguments for listen/read/write."""
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
            display(Markdown(f"**Unknown argument:** `{a}`"))
        i += 1
    return cmd, opts


@magics_class
class SerialMagic(Magics):

    @line_magic
    def serial(self, line, cell=None):
        """Magic cell %%serial for working with the serial port."""
        cmd, opts = _parse_serial_args(line)

        if cmd == "help" or cmd == "":
            display(Markdown(_help()))
            return

        if cmd not in ("listen", "read", "write"):
            display(Markdown("**Unknown command.**\n\n" + _help()))
            return

        try:
            bridge_manager.open_serial()

            if cmd == "listen":
                duration = opts["duration"]
                prefix = opts["prefix"]
                display(Markdown(
                    f"📡 **Listening**"
                    + (f", duration: {duration}s" if duration else ", duration: unlimited")
                    + (f", filter prefix: `{prefix}`" if prefix else "")
                ))
                bridge_manager.serial_listen(duration=duration, prefix=prefix)
                display(Markdown("✅ **Listening ended.**"))

            elif cmd == "read":
                lines = max(1, opts["lines"])
                for ln in bridge_manager.serial_read(lines=lines):
                    print(ln)

            elif cmd == "write":
                payload = opts["data"] if opts["data"] is not None else (cell or "")
                bridge_manager.serial_write(payload, append_newline=not opts["no_nl"])
                display(Markdown(f"✉️ **Sent:** `{payload.strip()}`"))

        except Exception as e:
            display(Markdown(f"**Error:** `{e}`"))
        finally:
            try:
                bridge_manager.close_serial()
            except Exception:
                pass


def load_ipython_extension(ipython):
    ipython.register_magics(SerialMagic)
