# code_manager.py
# Stores parts of Arduino code in memory and allows their management

from typing import List, Dict
import os

BLOCK_GAP = "\n"
SECTION_GAP = "\n\n"

GLOBAL_SECTION_SEPARATOR = "//**Global variables**\n"
FUNCTIONS_SECTION_SEPARATOR = "//**Functions**\n"
SETUP_SECTION_SEPARATOR = "//**Setup**\n"
LOOP_SECTION_SEPARATOR = "//**Loop**\n"

ALLOWED_SECTIONS = {"globals", "setup", "loop", "functions"}

class ArduinoCodeManager:
    def __init__(self):
        self.default()
    
    def default(self):
        # Initialize dictionary for code sections
        self.sections: Dict[str, Dict[str, str]] = {
            "globals": {},
            "setup": {},
            "loop": {},
            "functions": {}
        }
    
    def clear(self):
        """Clears all code in memory."""
        for key in self.sections:
            self.sections[key] = {}
     
    def find_cell(self, section: str, code: str) -> str|None:
        cell_id = None
        lines = code.split("\n")
        for k, codes in self.sections[section].items():
            for line in lines:
                if line not in codes:
                    break
                else:
                    cell_id = k
        
        return cell_id
    
    def replace_code(self, section: str, code: str):
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        
        cell_id = self.find_cell(section, code)
        if cell_id not in self.sections[section]:
            raise ValueError(f"Unknown cell: {cell_id}")
        
        self.remove_code(section, cell_id)
        self.add_code(section, cell_id, code)
    
    def remove_code(self, section: str, cell_id:str|None=None):
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        
        if cell_id and cell_id in self.sections[section]:
            del self.sections[section][cell_id]
        else:
            self.sections[section] = {}

    def add_code(self, section: str, cell_id:str, code: str):
        """
        Adds a code snippet to the selected section.
        section: one of ["globals", "setup", "loop", "functions"]
        code: code text (without leading and trailing spaces)
        """
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        self.sections[section][cell_id] = code.strip()

    def get_section(self, section: str) -> List[str]:
        """Returns all code snippets in the given section."""
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        cells = self.sections[section]
        return [cell for cell in cells.values()]

    def export_as_code(self) -> str:
        """
        Generates the complete Arduino code as text.
        """
        lines = []
        # Global variables
        lines.append(GLOBAL_SECTION_SEPARATOR)
        section = self.get_section("globals")
        lines.extend(section if len(section) > 0 else ["// No globals variables defined"])
        lines.append(BLOCK_GAP)
        
        # Functions
        lines.append(FUNCTIONS_SECTION_SEPARATOR)
        section = self.get_section("functions")
        lines.extend(section if len(section) > 0 else ["// No functions defined"])
        lines.append(BLOCK_GAP)

        # setup
        lines.append(SETUP_SECTION_SEPARATOR)
        lines.append("void setup() {")
        section = self.get_section("setup")
        setup_lines = section if len(section) > 0 else ["//Setup code goes here"]
        lines.extend(["\t" + line for line in setup_lines])
        lines.append("}")
        lines.append(BLOCK_GAP)

        # loop
        lines.append(LOOP_SECTION_SEPARATOR)
        lines.append("void loop() {")
        section = self.get_section("loop")
        loop_lines = section if len(section) > 0 else ["//Loop code goes here"]
        lines.extend(["\t" + line for line in loop_lines])
        lines.append("}")
        lines.append(BLOCK_GAP)

        return "\n".join(lines)
    
    def export_as_json(self) -> Dict[str, Dict[str, str]]:
        """
        Generates code as a dictionary, which can be easily serialized to JSON.
        """
        return self.sections
    
    def import_from_code(self, code: str):
        """
        Loads code from text and splits it into sections.
        code: complete Arduino code as text
        """
        self.clear()  # Clears existing code
        lines = code.splitlines()
        current_section = None
        cell_id = 0
        
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line or stripped_line in ["{", "}"]:
                continue
            elif stripped_line == GLOBAL_SECTION_SEPARATOR.strip():
                if current_section != "globals":
                    cell_id = 0
                    current_section = "globals"
                continue
            elif stripped_line == FUNCTIONS_SECTION_SEPARATOR.strip():
                if current_section != "functions":
                    cell_id = 0
                    current_section = "functions"
                continue
            elif stripped_line == SETUP_SECTION_SEPARATOR.strip() or stripped_line.startswith("void setup()"):
                if current_section != "setup":
                    cell_id = 0
                    current_section = "setup"
                continue
            elif stripped_line == LOOP_SECTION_SEPARATOR.strip() or stripped_line.startswith("void loop()"):
                if current_section != "loop":
                    cell_id = 0
                    current_section = "loop"
                continue
            else:
                if current_section:
                    self.sections[current_section][str(cell_id)] = stripped_line
                    cell_id += 1
                else:
                    raise ValueError("Code does not contain any section or is incorrectly formatted.")
                
    def import_from_json(self, json_data: Dict[str, Dict[str, str]]):
        """
        Loads code from a JSON dictionary.
        json_data: dictionary with code in the format {section: {cell_id: code}}
        """
        self.clear()
        # Check validity of sections
        valid_sections = {"globals", "setup", "loop", "functions"}
        if not all(section in valid_sections for section in json_data.keys()):
            raise ValueError("Invalid sections in JSON data.")
        self.sections = json_data
        
    
# Singleton instance
code_manager = ArduinoCodeManager()