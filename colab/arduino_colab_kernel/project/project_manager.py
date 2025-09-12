# project_manager.py
# Project management, generation and saving to .ino files

from typing import List, Dict, Optional
import os
import json

from arduino_colab_kernel.board.board_manager import board_manager  # global instance BoardManager
from arduino_colab_kernel.code.code_manager import code_manager  # global instance ArduinoCodeManager
from arduino_colab_kernel.bridge.bridge import bridge_manager  # global instance Bridge
from arduino_colab_kernel.bridge.bridge import LOCAL_MODE, REMOTE_MODE

from arduino_colab_kernel.code.ino_generator import InoGenerator
from arduino_colab_kernel.project.config import (
    DEFAULT_PROJECT_NAME,
    DEFAULT_PROJECTS_DIR,
    DEFAULT_LOGS_DIR
)

class ArduinoProjectManager:
    """
    Manages Arduino project lifecycle, including creation, loading, saving, and configuration.

    Attributes:
        project_name (str): Name of the current project.
        project_dir (str): Directory for the current project.
        logs_dir (str): Directory for logs.
        project_mode (str): Project mode ("local" or "remote").
        ino_generator (InoGenerator): Handles .ino file generation and loading.
    """
    def __init__(self):
        """
        Initializes the ArduinoProjectManager and sets up default values.
        """
        self.project_name = ""
        self.project_dir = ""
        self.logs_dir = ""
        self.project_mode = ""
        self.project_remote_url = ""
        self.ino_generator: InoGenerator = InoGenerator(prepare_dirs=False)
        
    def project_exists(self, project_name: str, project_dir: str = DEFAULT_PROJECTS_DIR) -> bool:
        """
        Checks if a project with the given name already exists.

        Args:
            project_name (str): Name of the project.
            project_dir (str): Path to the directory where projects are stored.

        Returns:
            bool: True if the project exists, False otherwise.
        """
        project_dir = os.path.join(project_dir, project_name)
        return os.path.exists(project_dir) and os.path.isdir(project_dir)
    
    def init_project(
        self,
        project_name: str = DEFAULT_PROJECT_NAME,
        projects_dir: str = DEFAULT_PROJECTS_DIR,
        project_mode: str = LOCAL_MODE,
        remote_url: Optional[str] = None,
        token: Optional[str] = None
    ):
        """
        Initializes a new project with the given name, directory, and mode.

        Args:
            project_name (str): Name of the project.
            projects_dir (str): Path to the directory where projects are stored.
            project_mode (str): Mode for the project ("local" or "remote").
            remote_url (Optional[str]): Remote server URL for remote mode.
            token (Optional[str]): API token for remote mode.

        Raises:
            ValueError: If the project mode is invalid.
            Exception: If directory or file operations fail.
        """
        self.project_name = project_name.strip()
        try:
            bridge_manager.set_mode(project_mode, remote_url=remote_url, token=token)
            self.project_mode = bridge_manager.mode
            self.project_remote_url = bridge_manager.remote_url
            
            self._set_project_dir(projects_dir)
            projects_dir_abs = self.get_project_dir(as_abs=True)
            self.ino_generator = InoGenerator(self.project_name, projects_dir_abs)
            board_manager.default()  # Select default board
            code_manager.default()   # Re-initialize code manager
            self.save()  # Save project
        except Exception as e:
            raise RuntimeError(f"Failed to initialize project: {e}")
    
    def load_project(
        self,
        project_name: str = DEFAULT_PROJECT_NAME,
        projects_dir: str = DEFAULT_PROJECTS_DIR,
        project_mode: str = LOCAL_MODE,
        remote_url: Optional[str] = None,
        token: Optional[str] = None
    ):
        """
        Loads an existing project, which will be used for file saving.

        Args:
            project_name (str): Name of the project (used for folder and file).
            projects_dir (str): Path to the directory where projects are stored.
            project_mode (str): Mode for the project ("local" or "remote").
            remote_url (Optional[str]): Remote server URL for remote mode.
            token (Optional[str]): API token for remote mode.

        Raises:
            ValueError: If the project mode is invalid.
            FileNotFoundError: If the project JSON file does not exist.
            Exception: If file operations fail.
        """
        self.project_name = project_name.strip()
        try:
            bridge_manager.set_mode(project_mode, remote_url=remote_url, token=token)
            self.project_mode = bridge_manager.mode
            self.project_remote_url = bridge_manager.remote_url
            
            self._set_project_dir(projects_dir)
            projects_dir_abs = self.get_project_dir(as_abs=True)
            self.ino_generator = InoGenerator(self.project_name, projects_dir_abs)
            json_file = os.path.join(projects_dir_abs, f"{self.project_name}.json")
            if not os.path.exists(json_file):
                raise FileNotFoundError(f"Project {self.project_name} does not contain any JSON project file.")
            with open(json_file, "r", encoding="utf-8") as f:
                json_data = json.load(f)
                self._configure(**json_data)
        except Exception as e:
            raise RuntimeError(f"Failed to load project: {e}")
        
    def status(self) -> str:
        """
        Returns the current project status.

        Returns:
            str: Status message with project name, mode, and directory. If mode == remote, also includes remote URL.
        """
        project_location = self.get_project_dir(as_abs=True) if self.project_dir else "Not set"
        return f"Project: `{self.project_name}` | Mode: `{self.project_mode}` [SERVER:{self.project_remote_url}] | Location: `{project_location}`"
    
    def delete_project(self):
        """
        Deletes the entire project directory and its contents.

        Raises:
            Exception: If file or directory operations fail.
        """
        code_manager.clear()
        sketch_dir = self.get_project_dir(as_abs=False)
        if os.path.exists(sketch_dir):
            try:
                # Recurse delete of the sketch directory and all its contents
                for root, dirs, files in os.walk(sketch_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(sketch_dir)
            except Exception as e:
                raise RuntimeError(f"Failed to delete project directory '{sketch_dir}': {e}")
    
    def _configure(self, **kwargs):
        """
        Configures the project from a dictionary.

        Args:
            **kwargs: Dictionary with project configuration.

        Raises:
            Exception: If configuration fails.
        """
        try:
            if "project_name" in kwargs:
                self.project_name = kwargs["project_name"]
            if "board" in kwargs:
                board_data: dict = kwargs["board"]
                board_manager.configure(**board_data)
            else:
                board_manager.default()
                
            if "code" in kwargs:
                code_data: dict = kwargs["code"]
                code_manager.import_from_json(code_data)
            else:
                code_manager.default()
        except Exception as e:
            raise RuntimeError(f"Failed to configure project: {e}")
            
    def clear(self, section: str | None = None, cell_id: str | None = None):
        """
        Clears the current project and code in memory.

        Args:
            section (str|None): Section to clear (optional).
            cell_id (str|None): Cell ID to clear (optional).

        Raises:
            Exception: If clearing code fails.
        """
        try:
            if section:
                code_manager.remove_code(section, cell_id)
            else:
                code_manager.clear()
        except Exception as e:
            raise RuntimeError(f"Failed to clear project code: {e}")
        
    def show(self) -> str:
        """
        Returns the current project code.

        Returns:
            str: The current Arduino code as text.
        """
        return code_manager.export_as_code()
    
    def export(self) -> dict:
        """
        Exports the current project settings as a dictionary.

        Returns:
            dict: Dictionary with project name, directory, ino file, board, and code.
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
        Saves the current code to a .ino file in the target directory and exports project JSON.

        Returns:
            str: Absolute path to the project directory.

        Raises:
            Exception: If saving code or project fails.
        """
        code = code_manager.export_as_code()
        try:
            self.ino_generator.export(code)
            # Export project
            project_json = self.export()
            projects_dir_abs = self.get_project_dir(as_abs=True)
            json_file = os.path.join(projects_dir_abs, f"{self.project_name}.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(project_json, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Failed to save project: {e}")
        return self.get_project_dir(as_abs=True)       
    
    def _set_project_dir(self, projects_dir: str):
        """
        Sets the target directory for saving .ino files and logs.

        Args:
            projects_dir (str): Path to the directory where sketches will be stored.

        Raises:
            Exception: If directory creation fails.
        """
        self.project_dir = os.path.join(projects_dir, self.project_name)
        self.logs_dir = os.path.join(self.project_dir, DEFAULT_LOGS_DIR)
        try:
            projects_dir_abs = self.get_project_dir(as_abs=True)
            os.makedirs(projects_dir_abs, exist_ok=True)
            logs_dir_abs = self.get_logs_dir(as_abs=True)
            os.makedirs(logs_dir_abs, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create project or logs directory: {e}")
    
    def get_project_dir(self, as_abs: bool = False) -> str:
        """
        Returns the path to the folder with sketches.

        Args:
            as_abs (bool): If True, returns absolute path, otherwise relative.

        Returns:
            str: Path to the project directory.
        """
        return os.path.abspath(self.project_dir) if as_abs else os.path.relpath(self.project_dir)
    
    def get_logs_dir(self, as_abs: bool = False) -> str:
        """
        Returns the path to the folder with logs.

        Args:
            as_abs (bool): If True, returns absolute path, otherwise relative.

        Returns:
            str: Path to the logs directory.
        """
        return os.path.abspath(self.logs_dir) if as_abs else os.path.relpath(self.logs_dir)
    
# Singleton for magics
project_manager = ArduinoProjectManager()