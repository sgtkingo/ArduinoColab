# magic_code.py
# Magie %%code – ukládá kód do sekcí (globals/setup/loop/functions) s volitelným ID buňky.
# Obsahuje přehlednou nápovědu přes _help_text().

import shlex
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.code.code_manager import code_manager
from arduino_colab_kernel.code.code_manager import ALLOWED_SECTIONS


def _help() -> str:
    # Vrací Markdown nápovědu jako text (volající si rozhodne o zobrazení)
    return """
### 🧩 Dostupné příkazy `%%code`

| Příkaz                   | Parametry                      | Popis                                                                 |
|--------------------------|--------------------------------|------------------------------------------------------------------------|
| **`%%code globals`**     | `[bunka_id]` *(volitelné)*     | Uloží kód do sekce **globals** (deklarace proměnných, konstant).      |
| **`%%code setup`**       | `[bunka_id]` *(volitelné)*     | Uloží kód do sekce **setup** (inicializace, běží jednou).             |
| **`%%code loop`**        | `[bunka_id]` *(volitelné)*     | Uloží kód do sekce **loop** (hlavní smyčka programu).                 |
| **`%%code functions`**   | `[bunka_id]` *(volitelné)*     | Uloží kód do sekce **functions** (pomocné funkce, knihovní kód).      |
| **`%%code help`** / `?`  | *(bez parametrů)*              | Zobrazí tuto nápovědu.                                                |

**Syntax:**
- `%%code <sekce>` nebo `%%code <sekce> <bunka_id>`
- Pokud **<bunka_id>** neuvedeš, použije se výchozí `"0"`.

**Povolené sekce:** `globals`, `setup`, `loop`, `functions`.

**Příklady:**
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
    @cell_magic
    def code(self, line, cell):
        # --- Parsování argumentů (bezpečně přes shlex) ---
        parts = shlex.split(line.strip()) if line else []
        section = parts[0].lower() if parts else None

        # --- Help / prázdný vstup ---
        if section in (None, "help", "?"):
            display(Markdown(_help()))
        # --- Validace sekce ---
        elif section in ALLOWED_SECTIONS:
            # --- ID buňky (volitelné) ---
            cell_id = parts[1] if len(parts) > 1 else "0"
            # --- Uložení kódu do správné sekce/buňky ---
            try:
                code_manager.add_code(section, cell_id, cell)
                display(Markdown(f"`Kód aktualizován` &nbsp;|&nbsp; sekce: `{section}`, buňka: `{cell_id}`."))
            except Exception as e:
                display(Markdown(f"**Chyba při ukládání kódu:** `{e}`"))
        else:
            display(Markdown(f"**Neznámá sekce kodu nebo příkaz:** `{section}`\n\n" + _help()))

def load_ipython_extension(ipython):
    ipython.register_magics(CodeMagics)