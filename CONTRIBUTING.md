# Contributing to Arduino Colab Kernel

First off, thanks for taking the time to contribute! 🎉  
This project aims to make Arduino/ESP32 development smooth inside Jupyter/Colab.

---

## Ways to contribute
- Report bugs and request features via **Issues**
- Improve docs (README, examples, tutorials)
- Submit pull requests (bug fixes, refactors, new magics)
- Add demos in `arduino_colab_kernel/demos/`

---

## Project structure (short)
```
arduino_colab_kernel/
  magic_board.py       # %board line magic
  magic_serial.py      # %%serial cell magic
  magic_project.py     # %project line magic
  magic_code.py        # %%code cell magic
  board_manager.py     # compile/upload, board selection
  board.py             # board config + composition
  serial_port.py       # serial I/O
  tools/               # optional: arduino-cli binaries, etc.
  demos/               # example sketches/projects
```
You may also find `utils_cli.py`, `code_weaver.py`, etc. depending on the branch.

---

## Development setup
1. **Fork** the repo and clone your fork
2. Create a virtual environment (recommended)
3. Install in editable mode:
   ```bash
   pip install -e .
   ```
4. (Optional) Install dev tools:
   ```bash
   pip install pytest black isort mypy
   ```

### Running in Jupyter
In a notebook:
```python
%load_ext arduino_colab_kernel.magic_board
%load_ext arduino_colab_kernel.magic_serial
%load_ext arduino_colab_kernel.magic_project
%load_ext arduino_colab_kernel.magic_code
```

---

## Coding guidelines
- Python ≥ 3.8
- Keep **identifiers in English**, **comments in Czech** (project convention)
- Run formatters before committing:
  ```bash
  black . && isort .
  ```
- Type hints for new/modified code are welcome (mypy-friendly)
- Keep public APIs stable; deprecate before removing

---

## Commit messages
- Use concise, descriptive messages:
  - `feat(board): add --log-file support`
  - `fix(serial): avoid crash on missing COM port`
  - `docs(readme): add quick start section`
- Reference issues like `Fixes #123` when applicable

---

## Pull request process
1. Open or reference an **Issue** describing the change
2. Ensure CI (if any) and linters pass locally
3. Add/update tests or demos when relevant
4. Update docs (`README.md`, help texts) if the UX changes
5. Keep PRs small and focused

---

## Reporting bugs
- Include OS, Python version, Jupyter variant
- Arduino board, port and `arduino-cli version`
- Minimal reproducible example (code + commands)
- Error logs (stdout/stderr) and steps to reproduce

---

## Code of Conduct
Be respectful, helpful and constructive.  
Report violations via Issues or by contacting the maintainer.

---

Thanks for contributing ❤️
