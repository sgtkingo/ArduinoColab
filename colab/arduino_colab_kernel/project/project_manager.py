# project_manager.py
# Project management, generation and saving to .ino files

from typing import List, Dict
import os
import json

from arduino_colab_kernel.board.board_manager import board_manager  # global instance BoardManager
from arduino_colab_kernel.code.code_manager import code_manager  # global instance ArduinoCodeManager
from arduino_colab_kernel.bridge.bridge import bridge_manager  # global instance Bridge
from arduino_colab_kernel.code.ino_generator import InoGenerator

DEFAULT_PROJECT_NAME = "sketch"
DEFAULT_PROJECTS_DIR = "./projects"
DEFAULT_LOGS_DIR = "logs"

LOCAL_MODE = "local"  # local mode (default)
REMOTE_MODE = "remote"  # remote mode (e.g. for cloud IDEs)

class ArduinoProjectManager:
    def __init__(self):
        # Project initialization
        self.project_name = ""
        self.project_dir = ""
        self.logs_dir = ""
        self.project_mode = LOCAL_MODE
        self.ino_generator:InoGenerator = InoGenerator(prepare_dirs=False)
        
    def project_exists(self, project_name: str, project_dir: str = DEFAULT_PROJECTS_DIR) -> bool:
        """
        Checks if a project with the given name already exists.
        project_name: name of the project
        project_dir: path to the directory where projects are stored
        """
        project_dir = os.path.join(project_dir, project_name)
        return os.path.exists(project_dir) and os.path.isdir(project_dir)
    
    def init_project(self, project_name: str = DEFAULT_PROJECT_NAME, projects_dir: str = DEFAULT_PROJECTS_DIR, project_mode: str = LOCAL_MODE):
        """
        Initializes a new project with the given name and sets the target directory.
        project_name: name of the project
        project_dir: path to the directory where projects are stored
        """
        self.project_name = project_name.strip()
        self.project_mode = project_mode.strip().lower()
        if self.project_mode not in (LOCAL_MODE, REMOTE_MODE):
            raise ValueError(f"Invalid project mode '{self.project_mode}'. Use '{LOCAL_MODE}' or '{REMOTE_MODE}'.")
        bridge_manager.set_mode(self.project_mode)
        self._set_project_dir(projects_dir)
        
        projects_dir_abs = self.get_project_dir(as_abs=True)
        self.ino_generator = InoGenerator(self.project_name, projects_dir_abs)
        
        board_manager.default() # Select default board
        code_manager.default()  # Re-initialize code manager
        self.save()  # Save project
    
    def load_project(self, project_name: str = DEFAULT_PROJECT_NAME, projects_dir: str = DEFAULT_PROJECTS_DIR, project_mode: str = LOCAL_MODE):
        """
        Loads an existing project, which will be used for file saving.
        project_name: name of the project (used for folder and file)
        """
        self.project_name = project_name.strip()
        self.project_mode = project_mode.strip().lower()
        if self.project_mode not in (LOCAL_MODE, REMOTE_MODE):
            raise ValueError(f"Invalid project mode '{self.project_mode}'. Use '{LOCAL_MODE}' or '{REMOTE_MODE}'.")
        bridge_manager.set_mode(self.project_mode)
        self._set_project_dir(projects_dir)
        
        projects_dir_abs = self.get_project_dir(as_abs=True)
        self.ino_generator = InoGenerator(self.project_name, projects_dir_abs)
        
        json_file = os.path.join(projects_dir_abs, f"{self.project_name}.json")
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"Project {self.project_name} does not contain any JSON project file.")
        with open(json_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            self._configure(**json_data)
        
    def get_project(self) -> tuple:
        """
        Returns the name and path of the current project.
        """
        return self.project_name, self.get_project_dir(as_abs=True)
    
    def delete_project(self):
        """Deletes the entire project."""
        code_manager.clear()
        sketch_dir = self.get_project_dir(as_abs=False)
        if os.path.exists(sketch_dir):
            # Recurse delete of the sketch directory and all its contents
            for root, dirs, files in os.walk(sketch_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(sketch_dir)
    
    def _configure(self, **kwargs):
        """Configures the project from a dictionary."""
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
            
    def clear(self, section:str|None = None, cell_id:str|None = None):
        """Clears the current project and code in memory."""
        if section:
            code_manager.remove_code(section, cell_id)
        code_manager.clear()
        
    def show(self) -> str:
        """Returns the current project code."""
        return code_manager.export_as_code()
    
    def export(self) -> dict:
        """
        Exports the current project settings as a dictionary.
        Returns a dictionary with the project name and path to the directory.
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
        Saves the current code to a .ino file in the target directory.
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
        Sets the target directory for saving .ino files.
        projects_dir: path to the directory where sketches will be stored
        """
        self.project_dir = os.path.join(projects_dir, self.project_name)
        self.logs_dir = os.path.join(self.project_dir, DEFAULT_LOGS_DIR)
            
        projects_dir_abs = self.get_project_dir(as_abs=True)
        os.makedirs(projects_dir_abs, exist_ok=True)
        
        logs_dir_abs = self.get_logs_dir(as_abs=True)
        os.makedirs(logs_dir_abs, exist_ok=True)
    
    def get_project_dir(self, as_abs = False) -> str:
        """
        Returns the path to the folder with sketches.
        as_abs: if True, returns absolute path, otherwise relative.
        """
        return os.path.abspath(self.project_dir) if as_abs else os.path.relpath(self.project_dir)
    
    def get_logs_dir(self, as_abs = False) -> str:
        """
        Returns the path to the folder with logs.
        as_abs: if True, returns absolute path, otherwise relative.
        """
        return os.path.abspath(self.logs_dir) if as_abs else os.path.relpath(self.logs_dir)
    
# Singleton for magics
project_manager = ArduinoProjectManager()