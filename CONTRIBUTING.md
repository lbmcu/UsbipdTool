# Contributing to UsbipdTool

Thanks for your interest in contributing! 🎉

This project is a small Windows GUI wrapper around
[usbipd-win](https://github.com/dorssel/usbipd-win). Contributions of all kinds
are welcome — bug reports, feature requests, documentation, and code.

## Code of Conduct

By participating, you agree to follow the
[Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please be kind and
respectful.

## Reporting Issues

- Search [existing issues](../../issues) first to avoid duplicates.
- Use the **Bug report** or **Feature request** template when opening an issue.
- Include as much context as possible: Windows version, `usbipd --version`,
  the device (`VID:PID`), and the log panel output.

## Development Setup

Requirements: Windows 10/11, Python 3.10+ (tested on 3.13),
[usbipd-win](https://github.com/dorssel/usbipd-win) and WSL 2.

```powershell
# 1. Create a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Run from source
python app.py
```

> On Windows, if `python` resolves to the Microsoft Store stub, use your real
> interpreter path instead.

## Project Layout

- `core/` — pure logic (usbipd wrapper, parsers, actions, config). No GUI dependency.
- `gui/` — PySide6 UI (main window, attach dialog, worker, i18n, theme).
- `resources/` — i18n dictionaries, QSS stylesheets, icon.

## Submitting a Pull Request

1. Fork the repository and create a feature branch.
2. Make focused changes and test them locally (`python app.py`).
3. Rebuild the EXE to make sure packaging still works:
   `python -m PyInstaller UsbipdTool.spec --noconfirm`.
4. Open a PR using the pull request template and describe your changes.

## Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Keep `core/` free of any Qt imports so it stays unit-testable.
- Keep UI strings in the i18n dictionaries (`resources/i18n/*.json`).

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
