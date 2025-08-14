# code_manager.py
# Uchovává části Arduino kódu v paměti a umožňuje jejich správu

from typing import List, Dict
import os

BLOCK_GAP = "\n"
SECTION_GAP = "\n\n"

GLOBAL_SECTION_SEPARATOR = "//**Global variables**\n"
FUNCTIONS_SECTION_SEPARATOR = "//**Functions**\n"
SETUP_SECTION_SEPARATOR = "//**Setup**\n"
LOOP_SECTION_SEPARATOR = "//**Loop**\n"


class ArduinoCodeManager:
    def __init__(self):
        self.reinit()
    
    def reinit(self):
        # Inicializace slovníku pro sekce kódu
        self.sections: Dict[str, Dict[str, str]] = {
            "globals": {},
            "setup": {},
            "loop": {},
            "functions": {}
        }
    
    def clear(self):
        """Vymaže celý kód v paměti."""
        for key in self.sections:
            self.sections[key] = {}

    def add_code(self, section: str, cell_id:str, code: str):
        """
        Přidá úryvek kódu do zvolené sekce.
        section: jedna z hodnot ["globals", "setup", "loop", "functions"]
        code: text kódu (bez úvodních a koncových mezer)
        """
        if section not in self.sections:
            raise ValueError(f"Neznámá sekce: {section}")
        self.sections[section][cell_id] = code.strip()

    def get_section(self, section: str) -> List[str]:
        """Vrací všechny úryvky kódu v dané sekci."""
        if section not in self.sections:
            raise ValueError(f"Neznámá sekce: {section}")
        cells = self.sections[section]
        return [cell for cell in cells.values()]

    def export_as_code(self) -> str:
        """
        Vygeneruje kompletní Arduino kód jako text.
        """
        lines = []
        # Globální proměnné
        lines.append(GLOBAL_SECTION_SEPARATOR)
        section = self.get_section("globals")
        lines.extend(section if len(section) > 0 else ["// No globals variables defined"])
        lines.append(BLOCK_GAP)
        
        # Funkce
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
        Vygeneruje kód jako slovník, který lze snadno serializovat do JSON.
        """
        return self.sections
    
    def import_from_code(self, code: str):
        """
        Načte kód z textu a rozdělí ho do sekcí.
        code: kompletní Arduino kód jako text
        """
        self.clear()  # Vymaže stávající kód
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
                    raise ValueError("Kód neobsahuje žádnou sekci nebo je nesprávně formátován.")
                
    def import_from_json(self, json_data: Dict[str, Dict[str, str]]):
        """
        Načte kód z JSON slovníku.
        json_data: slovník s kódem ve formátu {sekce: {id_buňky: kód}}
        """
        self.clear()
        # Kontrola platnosti sekcí
        valid_sections = {"globals", "setup", "loop", "functions"}
        if not all(section in valid_sections for section in json_data.keys()):
            raise ValueError("Neplatné sekce v JSON datech.")
        self.sections = json_data
        
    
# Singleton instance
code_manager = ArduinoCodeManager()