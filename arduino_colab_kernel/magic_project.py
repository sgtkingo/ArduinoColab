# magic_arduino.py
import os
import shlex
import json
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.project.project_manager import project_manager

@magics_class
class ProjectMagics(Magics):
    @line_magic
    def project(self, line):
        cmd = line.strip().lower()
        origin_cmd_parts = line.split(" ")
        if cmd.startswith("init"):
            project_name = "new_project" if len(origin_cmd_parts) < 2 else origin_cmd_parts[1]
            if project_manager.project_exists(project_name):
                display(Markdown(f"**Projekt s názvem `{project_name}` již existuje. Zvolte jiný název nebo použijte `%project load {project_name}` pro načtení existujícího projektu.**"))
                return
            project_manager.init_project(project_name)
            display(Markdown(f"`Projekt *{project_name}* úspěšně inicializován.`"))
        elif cmd.startswith("load "):
            project_name = origin_cmd_parts[1]
            project_manager.load_project(project_name)
            display(Markdown(f"`Načten projekt *{project_name}*.`"))
        elif cmd == "get":
            project_name, project_location = project_manager.get_project()
            display(Markdown(f"Projekt: **{project_name}** \t se nachází v: *{project_location}*"))
        elif cmd == "clear":
            project_manager.clear()
            display(Markdown("`Paměť kodu vymazána.`"))
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
            display(Markdown("**Použití: `%project init` `<název>` nebo `%project load` `<název>`, `get`, `clear`, `delete`, `show`, `export`**"))
        else:
            display(Markdown("**Neznámý příkaz. Povolené jsou: `project init`, `%project load` , `clear`, `delete`, `show`, `export`, `help` | `?`**"))

def load_ipython_extension(ipython):
    ipython.register_magics(ProjectMagics)