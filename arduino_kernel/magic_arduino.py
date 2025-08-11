# magic_arduino.py
import os
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import Markdown, display

from board_manager import BoardManager
from project_manager import ArduinoProjectManager

project_manager = ArduinoProjectManager()
board_manager = BoardManager()

@magics_class
class ArduinoMagics(Magics):
    @cell_magic
    def code(self, line, code):
        parts = line.strip().lower().split(" ")
        if len(parts) < 1:
            display(Markdown("**Použití: `%code <sekce>` nebo `%code <sekce> <bunka>`**"))
            return
        section = parts[0]
        cell_id = parts[1] if len(parts) > 1 else "0"
        if section in ["globals", "setup", "loop", "functions"]:
            project_manager.code_manager.add_code(section, cell_id, code)
            display(Markdown(f"`Kód aktualizován`, sekce: `{section}`, buňka: `{cell_id}`."))  
        elif section in ["help", "?"]:
            display(Markdown("**Použití: `%code globals`, `%code setup`, `%code loop`, `%code functions`**"))        
        else:
            display(Markdown("**Chybná sekce. Povolené jsou: `code globals`, `setup`, `loop`, `functions`, `help` | `?`**"))

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
            project_manager.code_manager.clear()
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
            code = project_manager.code_manager.export_as_code()
            display(Markdown(f"Project: **{project_name}**\n ```\n" + code + "\n```"))
        elif cmd == "export":
            # TODO: Export project as files tree
            file = project_manager.save()
            display(Markdown("```\n Project exported and saved as:" + file + "\n```"))
        elif cmd == "help" or "?":
            display(Markdown("**Použití: `%project init` `<název>` nebo `%project load` `<název>`, `get`, `clear`, `delete`, `show`, `export`**"))
        else:
            display(Markdown("**Neznámý příkaz. Povolené jsou: `project init`, `%project load` , `clear`, `delete`, `show`, `export`, `help` | `?`**"))
    
    @line_magic
    def board(self, line):
        cmd = line.strip().lower()
        origin_cmd_parts = line.split(" ")
        if cmd.startswith("select ") and len(origin_cmd_parts) >= 2:
            board_name = origin_cmd_parts[1]
            if len(origin_cmd_parts) > 2:
                board_port = origin_cmd_parts[2]
            else:
                # Default port if not specified
                board_port = "COM3"
                display(Markdown(f"`*Port nezadán, používám výchozí port: {board_port}`"))
            try:
                board_manager.select_board(board_name, board_port)
                display(Markdown(f"`Deska nastavena na: {board_name}, port: {board_port}`"))
            except ValueError as e:
                display(Markdown(f"**Chyba: {e}**"))
        elif cmd == "show":
            try:
                alias, fqbn, port = board_manager.get_selected_board()
                display(Markdown(f"`Aktuální deska: {alias} (FQBN: {fqbn}), port: {port}`"))
            except RuntimeError as e:
                display(Markdown(f"**Chyba: {e}**"))
        elif cmd == "list":
            boards = board_manager.list_boards()
            board_list = "\n".join([f"- **{name}**: *{fqbn}*" for name, fqbn in boards])
            display(Markdown(f"**Podporované desky:**\n{board_list}"))
        elif cmd == "compile":
            sketch_file = project_manager.save()
            sketch_dir = os.path.dirname(sketch_file)
            try:
                success = board_manager.compile(sketch_file)
                if success:
                    display(Markdown("`Kód úspěšně zkompilován.`"))
            except Exception as e:
                display(Markdown(f"**Chyba při kompilaci: {e}**"))
        elif cmd == "upload":
            sketch_file = project_manager.save()
            sketch_dir = os.path.dirname(sketch_file)
            try:
                success = board_manager.upload(sketch_file)
                if success:
                    display(Markdown("`Kód úspěšně nahrán na desku.`"))
            except Exception as e:
                display(Markdown(f"**Chyba při nahrávání: {e}**"))
        elif cmd == "help" or "?":
            display(Markdown("**Použití: `%board select` `<deska>` `<?port>`, `%board show`, `list`, `compile`, `upload`, `help` | `?`**"))
        else:
            display(Markdown("**Použití: `%board select` `<deska>` `<?port>` nebo `%board show`, `list`, `compile`, `upload`, `help` | `?`**"))

def load_ipython_extension(ipython):
    ipython.register_magics(ArduinoMagics)