# ino_generator.py
# Generuje a ukládá .ino soubor z připraveného kódu

import os

class InoGenerator:
    def __init__(self, filename:str = "sketch.ino", output_dir: str = "./arduino_sketch", prepare_dirs = True):
        fn = filename if filename.endswith(".ino") else filename + ".ino"
        self.output_dir = output_dir
        self.ino_file = os.path.join(output_dir, fn)
        
        if prepare_dirs:
            os.makedirs(self.output_dir, exist_ok=True)

    def export(self, code: str):
        """
        Zapíše kód do .ino souboru v cílovém adresáři.
        code: kompletní Arduino kód jako text
        """
        with open(self.ino_file, "w", encoding="utf-8") as f:
            f.write(code)
            
    def load(self) -> str:
        """
        Načte kód z .ino souboru.
        Vrací obsah souboru jako text.
        """
        ino_file = self.get_path()
        if not os.path.exists(ino_file):
            raise FileNotFoundError(f"Nenalezen žádný .ino soubor s cestou: {ino_file}.")
        
        with open(ino_file, "r", encoding="utf-8") as f:
            return f.read()

    def get_path(self) -> str:
        """Vrací cestu ke generovanému .ino souboru."""
        return  os.path.abspath(self.ino_file)