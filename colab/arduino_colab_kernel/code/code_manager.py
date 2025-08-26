# code_manager.py
# Stores parts of Arduino code in memory and allows their management

from typing import List, Dict

ARDUINO_LIB_INCLUDE = "#include <Arduino.h>\n"
BLOCK_GAP = "\n"
SECTION_GAP = "\n\n"

GLOBAL_SECTION_SEPARATOR = "//**Global variables**\n"
FUNCTIONS_SECTION_SEPARATOR = "//**Functions**\n"
SETUP_SECTION_SEPARATOR = "//**Setup**\n"
LOOP_SECTION_SEPARATOR = "//**Loop**\n"

ALLOWED_SECTIONS = {"globals", "setup", "loop", "functions"}

class ArduinoCodeManager:
    """
    Manages in-memory storage and manipulation of Arduino code sections.
    
    Attributes:
        sections (Dict[str, Dict[str, str]]): Dictionary of code sections, each containing cell_id: code.
    """
    def __init__(self):
        """
        Initializes the ArduinoCodeManager and sets up empty code sections.
        """
        self.default()
    
    def default(self):
        """
        Initializes or resets the dictionary for all code sections.
        
        Sections: 'globals', 'setup', 'loop', 'functions'.
        """
        self.sections: Dict[str, Dict[str, str]] = {
            "globals": {},
            "setup": {},
            "loop": {},
            "functions": {}
        }
    
    def clear(self):
        """
        Clears all code in memory for all sections.
        """
        for key in self.sections:
            self.sections[key] = {}
     
    def find_cell(self, section: str, code: str) -> str|None:
        """
        Finds the cell_id in a section that matches the given code.

        Args:
            section (str): Section name ('globals', 'setup', 'loop', 'functions').
            code (str): Code to search for.

        Returns:
            str | None: The cell_id if found, otherwise None.

        Raises:
            ValueError: If section is not found.
        """
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        cell_id = None
        lines = code.split("\n")
        for k, codes in self.sections[section].items():
            for line in lines:
                if line not in codes:
                    break
                else:
                    cell_id = k
        return cell_id
    
    def replace_code(self, section: str, code: str, cell_id:str|None=None):
        """
        Replaces code in a given section and cell.

        Args:
            section (str): Section name.
            code (str): New code to replace.
            cell_id (str|None): Cell ID to replace. If None, tries to find by code.

        Raises:
            ValueError: If section or cell_id is not found.
        """
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        if cell_id is None:
            cell_id = self.find_cell(section, code)
        if cell_id not in self.sections[section]:
            raise ValueError(f"Error when replacing code, unknown cell: {cell_id}")
        self.remove_code(section, cell_id)
        self.add_code(section, cell_id, code)
    
    def remove_code(self, section: str, cell_id:str|None=None):
        """
        Removes code from a section or clears the section.

        Args:
            section (str): Section name.
            cell_id (str|None): Cell ID to remove. If None, clears the section.

        Raises:
            ValueError: If section is not found.
        """
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        if cell_id is not None:
            if cell_id in self.sections[section]:
                del self.sections[section][cell_id]
            else:
                raise ValueError(f"Cell ID '{cell_id}' not found in section '{section}'.")
        else:
            self.sections[section] = {}

    def add_code(self, section: str, cell_id:str, code: str):
        """
        Adds a code snippet to the selected section.

        Args:
            section (str): One of ["globals", "setup", "loop", "functions"].
            cell_id (str): Identifier for the code cell.
            code (str): Code text (without leading and trailing spaces).

        Raises:
            ValueError: If section is not found.
        """
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        self.sections[section][cell_id] = code.strip()

    def get_section(self, section: str) -> List[str]:
        """
        Returns all code snippets in the given section.

        Args:
            section (str): Section name.

        Returns:
            List[str]: List of code snippets in the section.

        Raises:
            ValueError: If section is not found.
        """
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        cells = self.sections[section]
        return [cell for cell in cells.values()]

    def generate(self) -> str:
        """
        Generates the complete Arduino code as text from all sections.

        Returns:
            str: The generated Arduino code as a single string.
        """
        lines = []
        # Include Arduino lib
        lines.append(ARDUINO_LIB_INCLUDE)
        
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
    
    def export_as_code(self) -> str:
        """
        Exports the complete Arduino code as text.

        Returns:
            str: Exported code as text.
        """
        return self.generate()

    def export_as_json(self) -> Dict[str, Dict[str, str]]:
        """
        Generates code as a dictionary, which can be easily serialized to JSON.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary with code in the format {section: {cell_id: code}}.
        """
        return self.sections
    
    def import_from_code(self, code: str):
        """
        Loads code from text and splits it into sections.

        Args:
            code (str): Complete Arduino code as text.

        Raises:
            ValueError: If code does not contain any section or is incorrectly formatted.
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

        Args:
            json_data (Dict[str, Dict[str, str]]): Dictionary with code in the format {section: {cell_id: code}}.

        Raises:
            ValueError: If JSON data contains invalid sections.
        """
        self.clear()
        # Check validity of sections
        valid_sections = {"globals", "setup", "loop", "functions"}
        if not all(section in valid_sections for section in json_data.keys()):
            raise ValueError("Invalid sections in JSON data.")
        self.sections = json_data
        
    
# Singleton instance
code_manager = ArduinoCodeManager()