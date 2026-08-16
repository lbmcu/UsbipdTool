# UsbipdTool

**Attach USB devices to WSL 2 in a few clicks — a tiny GUI wrapper around `usbipd`.**

🌐 **Language:** [English](README.md) · [简体中文](README_ZH.md)

![Windows](https://img.shields.io/badge/platform-Windows-0078D6)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![PySide6](https://img.shields.io/badge/PySide6-6.8-41CD52)
![License](https://img.shields.io/badge/license-MIT-green)

UsbipdTool turns the repetitive "share → attach to WSL" command-line flow of
[usbipd-win](https://github.com/dorssel/usbipd-win) into a two-click operation.
It is aimed at embedded developers who forward USB-serial adapters
(CH340/CH343, CP210x, …) into WSL 2 — no more typing
`usbipd list` / `usbipd bind` / `usbipd attach` on every boot.

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Building from Source](#building-from-source)
- [Known Issues](#known-issues)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Features

- ✅ **Startup self-check** — detects `usbipd` and shows installation guidance
  (`winget install usbipd-win`) when it is missing.
- 🔍 **One-click scan** — lists USB devices (BUSID / VID:PID / description / state)
  via `usbipd state` (JSON), falling back to `usbipd list` for older versions.
- 🎯 **Context-aware actions** per device state:

  | State       | Actions                 |
  |-------------|-------------------------|
  | Not shared  | Bind (optional `--force`) |
  | Shared      | Attach to WSL · Unbind  |
  | Attached    | Detach · Unbind         |

- 🧲 **Attach dialog** — default distro or a dropdown of WSL distros, optional
  host IP (`--host-ip`), auto re-attach on replug (`--auto-attach`).
- 🪵 **Live log panel** — echoes the exact command run and its output.
- 🌐 **i18n** — English / 简体中文, switchable at runtime.
- 🎨 **Themes** — light / dark / follow system.
- 💾 **Persistent settings** — saved to `%APPDATA%\UsbipdTool\config.json`.

## Screenshots

<!-- TODO: add screenshots (main window, attach dialog, light/dark themes) -->

## Requirements

- Windows 10/11
- [usbipd-win](https://github.com/dorssel/usbipd-win) installed
  (`winget install usbipd-win`)
- WSL 2 with at least one distribution

## Quick Start

1. Make sure `usbipd-win` and WSL 2 are installed.
2. Grab `dist\UsbipdTool.exe` (prebuilt) or [build it yourself](#building-from-source).
3. Double-click the EXE — it embeds a `requireAdministrator` manifest, so you
   get a single UAC prompt at launch.
4. Click **Rescan**, then **Bind** the target device, then **Attach** it to WSL.
5. In WSL, the device appears as `/dev/ttyUSB*` (or `/dev/ttyACM*`) and is ready
   for serial debugging.

## How It Works

The app shells out to the `usbipd` CLI. The command mapping for **usbipd 5.3** is:

| Action                     | Command                                               |
|----------------------------|-------------------------------------------------------|
| Scan                       | `usbipd state` (fallback: `usbipd list`)              |
| Bind                       | `usbipd bind --busid <id> [--force]`                  |
| Unbind                     | `usbipd unbind --busid <id>`                          |
| Attach (default distro)    | `usbipd attach --wsl --busid <id>`                    |
| Attach (specific distro)   | `usbipd attach --wsl <distro> --busid <id>`           |
| Attach (advanced)          | append `--host-ip <ip>` / `--auto-attach`             |
| Detach                     | `usbipd detach --busid <id>`                          |

> **Note:** in usbipd 5.x, `attach` only supports WSL — the remote `--address`
> option was removed.

## Project Structure

```
UsbipdTool/
├── app.py                  # Entry point: detect usbipd → main window
├── core/                   # Pure logic, no GUI dependency, unit-testable
│   ├── models.py           # UsbDevice / WslDistro
│   ├── parser.py           # state JSON / list text / wsl list parsing
│   ├── usbipd.py           # command wrapper, output decoding, is_admin
│   ├── actions.py          # bind/unbind/attach/detach/scan
│   └── config.py           # config load/save
├── gui/                    # GUI layer
│   ├── main_window.py      # main window
│   ├── attach_dialog.py    # attach dialog
│   ├── worker.py           # QThread background runner
│   ├── i18n.py             # lightweight JSON-dictionary i18n
│   └── theme.py            # light/dark theme + palettes
├── resources/
│   ├── i18n/zh_CN.json     # Chinese dictionary
│   ├── i18n/en_US.json     # English dictionary
│   ├── styles_light.qss    # light stylesheet
│   ├── styles_dark.qss     # dark stylesheet
│   └── icon.ico            # app icon
├── requirements.txt
├── UsbipdTool.spec         # PyInstaller config (uac_admin)
├── README.md
└── README_ZH.md
```

## Configuration

Settings are stored in `%APPDATA%\UsbipdTool\config.json`:

| Key                   | Type   | Default | Description                                  |
|-----------------------|--------|---------|----------------------------------------------|
| `language`            | string | `""`    | `""` = system, `"zh_CN"`, `"en_US"`          |
| `theme`               | string | `""`    | `""` = system, `"light"`, `"dark"`           |
| `force_bind_default`  | bool   | `false` | default state of the "Force bind" checkbox   |
| `last_wsl_distro`     | string | `""`    | remembered WSL distribution                  |
| `last_host_ip`        | string | `""`    | remembered host IP                           |
| `auto_attach_default` | bool   | `false` | default for "auto re-attach"                 |

## Building from Source

> Requires Python 3.10+ (tested on 3.13). On Windows, if `python` resolves to the
> Microsoft Store stub, use your real interpreter path instead.

```powershell
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Generate the icon (optional, script provided)
python _make_icon.py

# 3. Build the single-file, windowed, UAC-elevated EXE
python -m PyInstaller UsbipdTool.spec --noconfirm
```

Output: `dist\UsbipdTool.exe` (~26 MB, single file).

## Known Issues

- **usbipd 5.x** removed `usbipd wsl list` and the remote `--address` option;
  `attach` now only targets WSL.
- With **USBPcap / hrdevmon** filter drivers installed, a plain `bind` may fail —
  use "Force bind" (`--force`); the app auto-suggests it on failure.
- Administrator rights are required; the EXE embeds a `requireAdministrator`
  manifest (single UAC prompt at launch).

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines. This project follows the
[Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Security

To report a security vulnerability, see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

## Acknowledgements

- [usbipd-win](https://github.com/dorssel/usbipd-win) — the underlying USB/IP tool.
