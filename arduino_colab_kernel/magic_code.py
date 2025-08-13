# magic_arduino.py
import os
import shlex
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.code.code_manager import code_manager

@magics_class
class CodeMagics(Magics):
    @cell_magic
    def code(self, line, code):
        parts = line.strip().lower().split(" ")
        if len(parts) < 1:
            display(Markdown("**Použití: `%code <sekce>` nebo `%code <sekce> <bunka>`**"))
            return
        section = parts[0]
        cell_id = parts[1] if len(parts) > 1 else "0"
        if section in ["globals", "setup", "loop", "functions"]:
            code_manager.add_code(section, cell_id, code)
            display(Markdown(f"`Kód aktualizován`, sekce: `{section}`, buňka: `{cell_id}`."))  
        elif section in ["help", "?"]:
            display(Markdown("**Použití: `%code globals`, `%code setup`, `%code loop`, `%code functions`**"))        
        else:
            display(Markdown("**Chybná sekce. Povolené jsou: `code globals`, `setup`, `loop`, `functions`, `help` | `?`**"))

def load_ipython_extension(ipython):
    ipython.register_magics(CodeMagics)