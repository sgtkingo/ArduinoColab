# ino_generator.py
# Generates and saves a .ino file from prepared code

import os

class InoGenerator:
    def __init__(self, filename:str = "sketch.ino", output_dir: str = "./arduino_sketch", prepare_dirs = True):
        """
        Initializes the InoGenerator.

        Args:
            filename (str): Name of the .ino file (default: "sketch.ino").
            output_dir (str): Directory to save the .ino file (default: "./arduino_sketch").
            prepare_dirs (bool): Whether to create the output directory if it doesn't exist.
        Raises:
            OSError: If the directory cannot be created.
        """
        fn = filename if filename.endswith(".ino") else filename + ".ino"
        self.output_dir = output_dir
        self.ino_file = os.path.join(output_dir, fn)
        
        if prepare_dirs:
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except Exception as e:
                raise OSError(f"Failed to create output directory '{self.output_dir}': {e}")

    def export(self, code: str):
        """
        Writes code to a .ino file in the target directory.

        Args:
            code (str): Complete Arduino code as text.

        Raises:
            OSError: If the file cannot be written.
        """
        try:
            with open(self.ino_file, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            raise OSError(f"Failed to write to .ino file '{self.ino_file}': {e}")
            
    def load(self) -> str:
        """
        Loads code from the .ino file.

        Returns:
            str: The file content as text.

        Raises:
            FileNotFoundError: If the .ino file does not exist.
            OSError: If the file cannot be read.
        """
        ino_file = self.get_path()
        if not os.path.exists(ino_file):
            raise FileNotFoundError(f"No .ino file found at path: {ino_file}.")
        
        try:
            with open(ino_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise OSError(f"Failed to read .ino file '{ino_file}': {e}")

    def get_path(self) -> str:
        """
        Returns the path to the generated .ino file.

        Returns:
            str: Absolute path to the .ino file.
        """
        return  os.path.abspath(self.ino_file)