# projekt_manager.py
# Správa projektů, generování a ukládání do .ino souborů

from typing import List, Dict
import os
import json

from arduino_colab_kernel.board.board_manager import board_manager  # globální instance BoardManager
from arduino_colab_kernel.code.code_manager import code_manager  # globální instance ArduinoCodeManager
from arduino_colab_kernel.code.ino_generator import InoGenerator

DEFAULT_PROJECTS_DIR = "./projects"

class ArduinoProjectManager:
    def __init__(self):
        # Inicializace projektu
        self.project_name = ""
        self.project_dir_rel = ""
        self.project_dir_abs = ""
        self.ino_generator:InoGenerator = InoGenerator(prepare_dirs=False)
        
    def project_exists(self, project_name: str, project_dir: str = DEFAULT_PROJECTS_DIR) -> bool:
        """
        Zjistí, zda projekt s daným názvem již existuje.
        project_name: název projektu
        project_dir: cesta k adresáři, kde se budou ukládat projekty
        """
        project_dir = os.path.join(project_dir, project_name)
        return os.path.exists(project_dir) and os.path.isdir(project_dir)
    
    def init_project(self, project_name: str, project_dir: str = DEFAULT_PROJECTS_DIR):
        """
        Inicializuje nový projekt s daným názvem a nastaví cílový adresář.
        project_name: název projektu
        project_dir: cesta k adresáři, kde se budou ukládat projekty
        """
        self.project_name = project_name.strip()
        self.set_project_dir(project_dir)
        
        self.ino_generator = InoGenerator(self.project_name, self.project_dir_abs)
        code_manager.clear()  # Vymaže kód v paměti
        self.save()  # Vytvoří prázdný .ino soubor
    
    def load_project(self, project_name: str, project_dir: str = DEFAULT_PROJECTS_DIR, from_json=True):
        """
        Načte starší project, který se použije při ukládání souborů.
        project_name: název projektu (používá se pro složku a soubor)
        """
        self.project_name = project_name.strip()
        self.set_project_dir(project_dir)
        
        self.ino_generator = InoGenerator(self.project_name, self.project_dir_abs)
        if from_json:
            json_file = os.path.join(self.project_dir_abs, f"{self.project_name}.json")
            if not os.path.exists(json_file):
                raise FileNotFoundError(f"Projekt {self.project_name} neobsahuje žádný JSON soubor.")
            with open(json_file, "r", encoding="utf-8") as f:
                json_code = json.load(f)
                code_manager.import_from_json(json_code)
        else:
            ino_file = self.ino_generator.get_path()
            if not os.path.exists(ino_file):
                raise FileNotFoundError(f"Projekt {self.project_name} neobsahuje žádný .ino soubor.")
            code = self.ino_generator.load_code()
            code_manager.import_from_code(code)
        
    def get_project(self) -> tuple:
        """
        Vrací název a cestu aktuálního projektu.
        """
        return self.project_name, self.get_project_dir(as_abs=True)
    
    def delete_project(self):
        """Vymaže celý projekt."""
        code_manager.clear()
        sketch_dir = self.get_project_dir(as_abs=False)
        if os.path.exists(sketch_dir):
            # Recurse delete of the sketech directory and all its contents
            for root, dirs, files in os.walk(sketch_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(sketch_dir)
    
    def clear(self):
        """Vymaže aktuální projekt a kód v paměti."""
        code_manager.clear()
    
    def export(self) -> dict:
        """
        Exportuje aktuální nastavení projektu jako slovník.
        Vrací slovník s názvem projektu a cestou k adresáři.
        """
        return {
            "project_name": self.project_name,
            "project_dir": self.get_project_dir(as_abs=True),
            "ino_file": self.ino_generator.get_path(),
            "board": board_manager.export(),
            "code": code_manager.export_as_json()
        }
    
    def save(self) -> str:
        """
        Uloží aktuální kód do .ino souboru v cílovém adresáři.
        """
        code = code_manager.export_as_code()
        self.ino_generator.write_code(code)
        
        # Export project
        project_json = self.export()
        
        json_file = os.path.join(self.project_dir_abs, f"{self.project_name}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(project_json, f, indent=4, ensure_ascii=False)
        
        return self.get_project_dir(as_abs=True)       
    
    def set_project_dir(self, projects_dir: str):
        """
        Nastaví cílový adresář pro ukládání .ino souborů.
        sketch_dir: cesta k adresáři, kde se budou ukládat skici
        """
        project_dir = os.path.join(projects_dir, self.project_name)
        self.project_dir_rel = project_dir
        self.project_dir_abs = os.path.abspath(project_dir)
        os.makedirs(self.project_dir_abs, exist_ok=True)
    
    def get_project_dir(self, as_abs = False) -> str:
        """
        Vrací cestu ke složce se skicemi.
        as_abs: pokud True, vrací absolutní cestu, jinak relativní.
        """
        return self.project_dir_abs if as_abs else self.project_dir_rel
    
# Singleton for magics
project_manager = ArduinoProjectManager()