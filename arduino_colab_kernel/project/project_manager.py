# projekt_manager.py
# Správa projektů, generování a ukládání do .ino souborů

from typing import List, Dict
import os
import json

from arduino_colab_kernel.board.board_manager import board_manager  # globální instance BoardManager
from arduino_colab_kernel.code.code_manager import code_manager  # globální instance ArduinoCodeManager
from arduino_colab_kernel.code.ino_generator import InoGenerator

DEFAULT_PROJECTS_DIR = "./projects"
DEFAULT_LOGS_DIR = "logs"

class ArduinoProjectManager:
    def __init__(self):
        # Inicializace projektu
        self.project_name = ""
        self.project_dir = ""
        self.logs_dir = ""
        self.ino_generator:InoGenerator = InoGenerator(prepare_dirs=False)
        
    def project_exists(self, project_name: str, project_dir: str = DEFAULT_PROJECTS_DIR) -> bool:
        """
        Zjistí, zda projekt s daným názvem již existuje.
        project_name: název projektu
        project_dir: cesta k adresáři, kde se budou ukládat projekty
        """
        project_dir = os.path.join(project_dir, project_name)
        return os.path.exists(project_dir) and os.path.isdir(project_dir)
    
    def init_project(self, project_name: str, projects_dir: str = DEFAULT_PROJECTS_DIR):
        """
        Inicializuje nový projekt s daným názvem a nastaví cílový adresář.
        project_name: název projektu
        project_dir: cesta k adresáři, kde se budou ukládat projekty
        """
        self.project_name = project_name.strip()
        self._set_project_dir(projects_dir)
        
        projects_dir_abs = self.get_project_dir(as_abs=True)
        self.ino_generator = InoGenerator(self.project_name, projects_dir_abs)
        
        board_manager.default() # Vyber defaultní desku
        code_manager.default()  # Re-inicializuje code manager
        self.save()  # Ulož projekt
    
    def load_project(self, project_name: str, projects_dir: str = DEFAULT_PROJECTS_DIR):
        """
        Načte starší project, který se použije při ukládání souborů.
        project_name: název projektu (používá se pro složku a soubor)
        """
        self.project_name = project_name.strip()
        self._set_project_dir(projects_dir)
        
        projects_dir_abs = self.get_project_dir(as_abs=True)
        self.ino_generator = InoGenerator(self.project_name, projects_dir_abs)
        
        json_file = os.path.join(projects_dir_abs, f"{self.project_name}.json")
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"Projekt {self.project_name} neobsahuje žádný JSON projektový soubor.")
        with open(json_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            self._configure(**json_data)
        
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
    
    def _configure(self, **kwargs):
        """Nakofiguruje projekt ze slovníku."""
        if "project_name" in kwargs:
            self.project_name = kwargs["project_name"]
            
        if "board" in kwargs:
            board_data:dict = kwargs["board"]
            board_manager.configure(**board_data)
        else:
            board_manager.default()
            
        if "code" in kwargs:
            code_data:dict = kwargs["code"]
            code_manager.import_from_json(code_data)
        else:
            code_manager.default()
            
    def clear(self):
        """Vymaže aktuální projekt a kód v paměti."""
        code_manager.clear()
        
    def show(self) -> str:
        """Vrátí aktuální kody projektu"""
        return code_manager.export_as_code()
    
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
        self.ino_generator.export(code)
        
        # Export project
        project_json = self.export()
        projects_dir_abs = self.get_project_dir(as_abs=True)
        json_file = os.path.join(projects_dir_abs, f"{self.project_name}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(project_json, f, indent=4, ensure_ascii=False)
        
        return self.get_project_dir(as_abs=True)       
    
    def _set_project_dir(self, projects_dir: str):
        """
        Nastaví cílový adresář pro ukládání .ino souborů.
        projects_dir: cesta k adresáři, kde se budou ukládat skici
        """
        self.project_dir = os.path.join(projects_dir, self.project_name)
        self.logs_dir = os.path.join(self.project_dir, DEFAULT_LOGS_DIR)
            
        projects_dir_abs = self.get_project_dir(as_abs=True)
        os.makedirs(projects_dir_abs, exist_ok=True)
        
        logs_dir_abs = self.get_logs_dir(as_abs=True)
        os.makedirs(logs_dir_abs, exist_ok=True)
    
    def get_project_dir(self, as_abs = False) -> str:
        """
        Vrací cestu ke složce se skicemi.
        as_abs: pokud True, vrací absolutní cestu, jinak relativní.
        """
        return os.path.abspath(self.project_dir) if as_abs else os.path.relpath(self.project_dir)
    
    def get_logs_dir(self, as_abs = False) -> str:
        """
        Vrací cestu ke složce s logama.
        as_abs: pokud True, vrací absolutní cestu, jinak relativní.
        """
        return os.path.abspath(self.logs_dir) if as_abs else os.path.relpath(self.logs_dir)
    
# Singleton for magics
project_manager = ArduinoProjectManager()