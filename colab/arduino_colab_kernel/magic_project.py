# magic_arduino.py
import os
import shlex
import json
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.project.project_manager import project_manager
from arduino_colab_kernel.project.project_manager import DEFAULT_PROJECT_NAME

def _help() -> str:
    text = """
### 📘 Dostupné příkazy `%project`

| Příkaz                        | Parametry                        | Popis                                                                 |
|-------------------------------|----------------------------------|----------------------------------------------------------------------|
| **`%project init`**           | `[název]`                        | Vytvoří nový projekt s daným názvem.                                 |
| **`%project load`**           | `[název]`                        | Načte existující projekt podle názvu.                                |
| **`%project clear`**          | `[sekce] [buňka]`*(volitelné)*   | Smaže obsah vybrané sekce, případně konkrétní buňky.                 |
| **`%project get`**            | *(bez parametrů)*                | Získá informace o aktuálním projektu.                                |
| **`%project delete`**         | *(bez parametrů)*                | Smaže celý aktuální projekt.                                         |
| **`%project show`**           | *(bez parametrů)*                | Zobrazí přehled projektu (sekce, buňky, kód).                        |
| **`%project export`**         | *(bez parametrů)*                | Exportuje projekt do souboru a uloží jej.                            |
| **`%project help`** / **`?`** | *(bez parametrů)*                | Zobrazí tuto nápovědu.                                               |
    """
    return text

@magics_class
class ProjectMagics(Magics):
    @line_magic
    def project(self, line):
        cmd = line.strip().lower()
        origin_cmd_parts = line.split(" ")
        if cmd.startswith("init"):
            project_name = DEFAULT_PROJECT_NAME if len(origin_cmd_parts) < 2 else origin_cmd_parts[1]
            if project_manager.project_exists(project_name):
                display(Markdown(f"**Projekt s názvem `{project_name}` již existuje. Zvolte jiný název nebo použijte `%project load {project_name}` pro načtení existujícího projektu.**"))
                return
            project_manager.init_project(project_name)
            display(Markdown(f"`Projekt *{project_name}* úspěšně inicializován.`"))
        elif cmd.startswith("load"):
            project_name = DEFAULT_PROJECT_NAME if len(origin_cmd_parts) < 2 else origin_cmd_parts[1]
            if not project_manager.project_exists(project_name):
                display(Markdown(f"**Projekt s názvem `{project_name}` neexistuje! Zvolte jiný název nebo použijte `%project init {project_name}` pro založení nového projektu.**"))
                return
            project_manager.load_project(project_name)
            display(Markdown(f"`Načten projekt *{project_name}*.`"))
        elif cmd.startswith("clear"):
            section_name = None if len(origin_cmd_parts) < 2 else origin_cmd_parts[1]
            cell_id = None if len(origin_cmd_parts) < 3 else origin_cmd_parts[2]
            project_manager.clear(section=section_name, cell_id=cell_id)
            display(Markdown("`Paměť kodu vymazána.`"))
        elif cmd == "get":
            project_name, project_location = project_manager.get_project()
            display(Markdown(f"Projekt: **{project_name}** \t se nachází v: *{project_location}*"))
        elif cmd == "delete":
            project_manager.delete_project()
            user_affirmation = input("Opravdu chcete smazat celý projekt? (y/n): ").strip().lower()
            if user_affirmation == 'y':
                project_manager.delete_project()
                display(Markdown("`Projekt smazán!`"))
            else:
                display(Markdown("`Smazání projektu zrušeno...`"))
        elif cmd == "show":
            project_name = project_manager.project_name if project_manager.project_name else "Není nastaven žádný projekt"
            code = project_manager.show()
            display(Markdown(f"Project: **{project_name}**\n ```\n" + code + "\n```"))
        elif cmd == "export":
            file = project_manager.save()
            display(Markdown("```\n Project exported and saved as:" + file + "\n```"))
        elif cmd == "help" or "?":
            display(Markdown(_help()))
        else:
           display(Markdown(f"**Neznámý příkaz:** `{cmd}`\n\n" + _help()))

def load_ipython_extension(ipython):
    ipython.register_magics(ProjectMagics)