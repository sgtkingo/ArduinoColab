# magic_code.py
# Magic %%code – saves code into sections (globals/setup/loop/functions) with optional cell ID.
# Contains clear help via _help_text().

import shlex
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.code.code_manager import code_manager
from arduino_colab_kernel.project.project_manager import project_manager
from arduino_colab_kernel.code.code_manager import ALLOWED_SECTIONS


def _help() -> str:
    """
    Returns Markdown help text for the %%code magic command.

    Returns:
        str: Markdown-formatted help text.
    """
    return """
### 🧩 Available `%%code` commands

| Command                  | Parameters                     | Description                                                             |
|--------------------------|--------------------------------|-------------------------------------------------------------------------|
| **`%%code globals`**     | `[cell_id]` *(optional)*       | Saves code to **globals** section (variable/constant declarations).     |
| **`%%code setup`**       | `[cell_id]` *(optional)*       | Saves code to **setup** section (initialization, runs once).            |
| **`%%code loop`**        | `[cell_id]` *(optional)*       | Saves code to **loop** section (main program loop).                     |
| **`%%code functions`**   | `[cell_id]` *(optional)*       | Saves code to **functions** section (helper/library code).              |
| **`%%code help`** / `?`  | *(no parameters)*              | Shows this help.                                                        |

**Syntax:**
- `%%code <section>` or `%%code <section> <cell_id>`
- If **<cell_id>** is not provided, the default `"0"` is used.

**Allowed sections:** `globals`, `setup`, `loop`, `functions`.

**Examples:**
```python
%%code globals
int led = 13;

%%code setup 1
pinMode(led, OUTPUT);

%%code loop
digitalWrite(led, HIGH); delay(500);
digitalWrite(led, LOW);  delay(500);

%%code functions
int readSensor() { return analogRead(A0); }
"""
@magics_class
class CodeMagics(Magics):
    """
    Implements the %%code cell magic for saving code into Arduino code sections.

    Methods:
        code(line, cell): Handles the %%code magic cell.
    """

    @cell_magic
    def code(self, line, cell):
        """
        Handles the %%code magic cell.

        Args:
            line (str): The command line after %%code (section and optional cell_id).
            cell (str): The code content of the cell.

        Returns:
            None

        Raises:
            Does not raise; all exceptions are caught and displayed as Markdown.
        """
        # --- Argument parsing (safely via shlex) ---
        try:
            parts = shlex.split(line.strip()) if line else []
            section = parts[0].lower() if parts else None
        except Exception as e:
            display(Markdown(f"**Error parsing arguments:** `{e}`"))
            return

        # --- Help / empty input ---
        if section in (None, "help", "?"):
            display(Markdown(_help()))
        # --- Section validation ---
        elif section in ALLOWED_SECTIONS:
            # --- Cell ID (optional) ---
            cell_id = parts[1] if len(parts) > 1 else "0"
            # --- Save code to correct section/cell ---
            try:
                code_manager.add_code(section, cell_id, cell)
                # Save changes
                project_manager.save()
                display(Markdown(f"`Code updated` &nbsp;|&nbsp; section: `{section}`, cell: `{cell_id}`."))
            except Exception as e:
                display(Markdown(f"**Error saving code:** `{e}`"))
        else:
            display(Markdown(f"**Unknown code section or command:** `{section}`\n\n" + _help()))

def load_ipython_extension(ipython):
    """
    Registers the CodeMagics class as an IPython extension.

    Args:
        ipython: The IPython interactive shell instance.

    Returns:
        None
    """
    ipython.register_magics(CodeMagics)