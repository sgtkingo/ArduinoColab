# magic_arduino.py
import os
import shlex
import json
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import Markdown, display

from arduino_colab_kernel.project.project_manager import project_manager
from arduino_colab_kernel.project.project_manager import DEFAULT_PROJECT_NAME, LOCAL_MODE, REMOTE_MODE

def _help() -> str:
    """
    Returns Markdown help text for the %project magic command.

    Returns:
        str: Markdown-formatted help text.
    """
    text = """
### 📘 Available `%project` commands

| Command                        | Parameters                        | Description                                                           |
|-------------------------------|-----------------------------------|-----------------------------------------------------------------------|
| **`%project init`**           | `[name] [--mode local/remote]`     | Creates a new project with the given name and mode.                   |
| **`%project load`**           | `[name] [--mode local/remote] [--remote_url <URL>] [--token <API_TOKEN>]`     | Loads an existing project by name and mode. For mode `remote` please provide token using `--token <YOUR_API_TOKEN_HERE>`. You can also provide remote server url address using `--remote_url <YOUR_REMOTE_SERVER_ADDRESS_HERE>` (*Optional*)|
| **`%project clear`**          | `[section] [cell]`*(optional)*    | Clears the content of the selected section or a specific cell.        |
| **`%project get`**            | *(no parameters)*                 | Gets information about the current project.                           |
| **`%project delete`**         | *(no parameters)*                 | Deletes the entire current project.                                   |
| **`%project show`**           | *(no parameters)*                 | Displays a project overview (sections, cells, code).                  |
| **`%project export`**         | *(no parameters)*                 | Exports the project to a file and saves it.                           |
| **`%project help`** / **`?`** | *(no parameters)*                 | Shows this help.                                                      |
    """
    return text

def _parse_name_mode(args):
    """
    Parse [name] [--mode local|remote] [--remote_url <url>] [--token <token>] from args list.

    Args:
        args (list): List of arguments.

    Returns:
        tuple: (name, mode, remote_url, token) where name is the project name, mode is the project mode,
               remote_url is the URL for remote mode, and token is the authentication token.
    """
    name = DEFAULT_PROJECT_NAME
    mode = LOCAL_MODE
    remote_url = None
    token = None
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1].lower()
            i += 2
        elif args[i] == "--remote_url" and i + 1 < len(args):
            remote_url = args[i + 1]
            i += 2
        elif args[i] == "--token" and i + 1 < len(args):
            token = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            name = args[i]
            i += 1
        else:
            i += 1
    if mode not in (LOCAL_MODE, REMOTE_MODE):
        mode = LOCAL_MODE
    return name, mode, remote_url, token

@magics_class
class ProjectMagics(Magics):
    """
    Implements the %project magic command for project management.

    Methods:
        project(line): Handles the %project magic command.
    """

    @line_magic
    def project(self, line):
        """
        Handles the %project magic command.

        Args:
            line (str): The command line input after %project.

        Returns:
            None

        Raises:
            Does not raise; all exceptions are caught and displayed as Markdown.
        """
        try:
            args = shlex.split(line)
        except Exception as e:
            display(Markdown(f"**Error parsing arguments:** `{e}`"))
            return

        cmd = args[0].lower() if args else ""
        rest = args[1:] if len(args) > 1 else []

        try:
            if cmd.startswith("init"):
                # Create a new project
                name, mode, remote_url, token = _parse_name_mode(rest)
                if project_manager.project_exists(name):
                    display(Markdown(f"**A project named `{name}` already exists. Choose another name or use `%project load {name}` to load the existing project.**"))
                    return
                try:
                    project_manager.init_project(name, project_mode=mode, remote_url=remote_url, token=token)
                    display(Markdown(f"`Project *{name}* successfully initialized in mode: {mode}.`"))
                except Exception as e:
                    display(Markdown(f"**Error initializing project:** `{e}`"))
            elif cmd.startswith("load"):
                # Load an existing project
                name, mode, remote_url, token = _parse_name_mode(rest)
                if not project_manager.project_exists(name):
                    display(Markdown(f"**A project named `{name}` does not exist! Choose another name or use `%project init {name}` to create a new project.**"))
                    return
                try:
                    project_manager.load_project(name, project_mode=mode, remote_url=remote_url, token=token)
                    display(Markdown(f"`Project *{name}* loaded in mode: {mode}.`"))
                except Exception as e:
                    display(Markdown(f"**Error loading project:** `{e}`"))
            elif cmd.startswith("clear"):
                # Clear code memory or section/cell
                section_name = rest[0] if len(rest) > 0 else None
                cell_id = rest[1] if len(rest) > 1 else None
                try:
                    project_manager.clear(section=section_name, cell_id=cell_id)
                    display(Markdown("`Code memory cleared.`"))
                except Exception as e:
                    display(Markdown(f"**Error clearing code:** `{e}`"))
            elif cmd == "get":
                # Show project info
                try:
                    project_name, project_location = project_manager.get_project()
                    display(Markdown(f"Project: **{project_name}** \t is located at: *{project_location}*"))
                except Exception as e:
                    display(Markdown(f"**Error getting project info:** `{e}`"))
            elif cmd == "delete":
                # Delete the project after user confirmation
                try:
                    user_affirmation = input("Do you really want to delete the entire project? (y/n): ").strip().lower()
                    if user_affirmation == 'y':
                        project_manager.delete_project()
                        display(Markdown("`Project deleted!`"))
                    else:
                        display(Markdown("`Project deletion cancelled...`"))
                except Exception as e:
                    display(Markdown(f"**Error deleting project:** `{e}`"))
            elif cmd == "show":
                # Show project code
                try:
                    project_name = project_manager.project_name if project_manager.project_name else "No project set"
                    code = project_manager.show()
                    display(Markdown(f"Project: **{project_name}**\n ```\n" + code + "\n```"))
                except Exception as e:
                    display(Markdown(f"**Error showing project code:** `{e}`"))
            elif cmd == "export":
                # Export and save project
                try:
                    file = project_manager.save()
                    display(Markdown("```\n Project exported and saved as:" + file + "\n```"))
                except Exception as e:
                    display(Markdown(f"**Error exporting project:** `{e}`"))
            elif cmd == "help" or cmd == "?":
                display(Markdown(_help()))
            else:
                display(Markdown(f"**Unknown command:** `{cmd}`\n\n" + _help()))
        except Exception as e:
            display(Markdown(f"**Error:** `{e}`"))

def load_ipython_extension(ipython):
    """
    Registers the ProjectMagics class as an IPython extension.

    Args:
        ipython: The IPython interactive shell instance.

    Returns:
        None
    """
    ipython.register_magics(ProjectMagics)