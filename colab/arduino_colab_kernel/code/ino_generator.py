# ino_generator.py
# Generates and saves a .ino file from prepared code

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
        Writes code to a .ino file in the target directory.
        code: complete Arduino code as text
        """
        with open(self.ino_file, "w", encoding="utf-8") as f:
            f.write(code)
            
    def load(self) -> str:
        """
        Loads code from the .ino file.
        Returns the file content as text.
        """
        ino_file = self.get_path()
        if not os.path.exists(ino_file):
            raise FileNotFoundError(f"No .ino file found at path: {ino_file}.")
        
        with open(ino_file, "r", encoding="utf-8") as f:
            return f.read()

    def get_path(self) -> str:
        """Returns the path to the generated .ino file."""
        return  os.path.abspath(self.ino_file)