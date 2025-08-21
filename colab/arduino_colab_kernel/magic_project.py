# magic_arduino.py
import os
import shlex
import json
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.project.project_manager import project_manager
from arduino_colab_kernel.project.project_manager import DEFAULT_PROJECT_NAME, LOCAL_MODE, REMOTE_MODE

def _help() -> str:
    text = """
### 📘 Available `%project` commands

| Command                        | Parameters                        | Description                                                           |
|-------------------------------|-----------------------------------|-----------------------------------------------------------------------|
| **`%project init`**           | `[name] [--mode local|remote]`     | Creates a new project with the given name and mode.                   |
| **`%project load`**           | `[name] [--mode local|remote]`     | Loads an existing project by name and mode.                           |
| **`%project clear`**          | `[section] [cell]`*(optional)*    | Clears the content of the selected section or a specific cell.        |
| **`%project get`**            | *(no parameters)*                 | Gets information about the current project.                           |
| **`%project delete`**         | *(no parameters)*                 | Deletes the entire current project.                                   |
| **`%project show`**           | *(no parameters)*                 | Displays a project overview (sections, cells, code).                  |
| **`%project export`**         | *(no parameters)*                 | Exports the project to a file and saves it.                           |
| **`%project help`** / **`?`** | *(no parameters)*                 | Shows this help.                                                      |
    """
    return text

def _parse_name_mode(args):
    """Parse [name] [--mode local|remote] from args list."""
    name = DEFAULT_PROJECT_NAME
    mode = LOCAL_MODE
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1].lower()
            i += 2
        elif not args[i].startswith("--"):
            name = args[i]
            i += 1
        else:
            i += 1
    if mode not in (LOCAL_MODE, REMOTE_MODE):
        mode = LOCAL_MODE
    return name, mode

@magics_class
class ProjectMagics(Magics):
    @line_magic
    def project(self, line):
        args = shlex.split(line)
        cmd = args[0].lower() if args else ""
        rest = args[1:] if len(args) > 1 else []

        if cmd.startswith("init"):
            name, mode = _parse_name_mode(rest)
            if project_manager.project_exists(name):
                display(Markdown(f"**A project named `{name}` already exists. Choose another name or use `%project load {name}` to load the existing project.**"))
                return
            project_manager.init_project(name, project_mode=mode)
            display(Markdown(f"`Project *{name}* successfully initialized in mode: {mode}.`"))
        elif cmd.startswith("load"):
            name, mode = _parse_name_mode(rest)
            if not project_manager.project_exists(name):
                display(Markdown(f"**A project named `{name}` does not exist! Choose another name or use `%project init {name}` to create a new project.**"))
                return
            project_manager.load_project(name, project_mode=mode)
            display(Markdown(f"`Project *{name}* loaded in mode: {mode}.`"))
        elif cmd.startswith("clear"):
            section_name = rest[0] if len(rest) > 0 else None
            cell_id = rest[1] if len(rest) > 1 else None
            project_manager.clear(section=section_name, cell_id=cell_id)
            display(Markdown("`Code memory cleared.`"))
        elif cmd == "get":
            project_name, project_location = project_manager.get_project()
            display(Markdown(f"Project: **{project_name}** \t is located at: *{project_location}*"))
        elif cmd == "delete":
            project_manager.delete_project()
            user_affirmation = input("Do you really want to delete the entire project? (y/n): ").strip().lower()
            if user_affirmation == 'y':
                project_manager.delete_project()
                display(Markdown("`Project deleted!`"))
            else:
                display(Markdown("`Project deletion cancelled...`"))
        elif cmd == "show":
            project_name = project_manager.project_name if project_manager.project_name else "No project set"
            code = project_manager.show()
            display(Markdown(f"Project: **{project_name}**\n ```\n" + code + "\n```"))
        elif cmd == "export":
            file = project_manager.save()
            display(Markdown("```\n Project exported and saved as:" + file + "\n```"))
        elif cmd == "help" or cmd == "?":
            display(Markdown(_help()))
        else:
            display(Markdown(f"**Unknown command:** `{cmd}`\n\n" + _help()))

def load_ipython_extension(ipython):
    ipython.register_magics(ProjectMagics)