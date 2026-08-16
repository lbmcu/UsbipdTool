# UsbipdTool

**把 USB 设备附加到 WSL 2，只需点几下 —— 一个基于 `usbipd` 的轻量图形工具。**

🌐 **语言：** [English](README.md) · [简体中文](README_ZH.md)

![Windows](https://img.shields.io/badge/platform-Windows-0078D6)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![PySide6](https://img.shields.io/badge/PySide6-6.8-41CD52)
![License](https://img.shields.io/badge/license-MIT-green)

UsbipdTool 把 [usbipd-win](https://github.com/dorssel/usbipd-win) 那套
「共享 → 附加到 WSL」的命令行流程，封装成「点几下按钮」的操作，面向需要在
WSL 2 里透传 USB 转串口芯片（CH340/CH343、CP210x 等）的嵌入式开发者——
从此不用每次开机都敲 `usbipd list` / `usbipd bind` / `usbipd attach`。

## 目录

- [功能特性](#功能特性)
- [界面截图](#界面截图)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [工作原理](#工作原理)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [从源码构建](#从源码构建)
- [已知问题](#已知问题)
- [贡献指南](#贡献指南)
- [安全](#安全)
- [许可证](#许可证)

## 功能特性

- ✅ **启动自检** — 自动检测 `usbipd`，缺失时给出 `winget install usbipd-win` 安装指引。
- 🔍 **一键扫描** — 通过 `usbipd state`（JSON）列出 USB 设备（BUSID / VID:PID / 描述 / 状态），旧版本回退 `usbipd list`。
- 🎯 **按状态智能操作**：

  | 状态     | 可用操作                  |
  |----------|---------------------------|
  | 未共享   | 绑定（可选 `--force`）    |
  | 已共享   | 附加到 WSL · 解绑         |
  | 已附加   | 分离 · 解绑               |

- 🧲 **附加对话框** — 默认发行版 / 指定发行版下拉、可选主机 IP（`--host-ip`）、设备重插自动重附（`--auto-attach`）。
- 🪵 **实时日志面板** — 回显实际执行的命令与结果。
- 🌐 **多语言** — 英文 / 简体中文，运行时可切换。
- 🎨 **主题** — 浅色 / 深色 / 跟随系统。
- 💾 **配置持久化** — 保存到 `%APPDATA%\UsbipdTool\config.json`。

## 界面截图

<!-- TODO: 添加截图（主窗口、附加对话框、浅色/深色主题） -->

## 环境要求

- Windows 10/11
- 已安装 [usbipd-win](https://github.com/dorssel/usbipd-win)（`winget install usbipd-win`）
- WSL 2 已安装并至少有一个发行版

## 快速开始

1. 确保已安装 `usbipd-win` 与 WSL 2。
2. 取用 `dist\UsbipdTool.exe`（预构建产物），或[自行构建](#从源码构建)。
3. 双击 EXE —— 程序内嵌 `requireAdministrator` 清单，启动时弹一次 UAC。
4. 点「重新扫描」，对目标设备依次点「绑定」「附加」。
5. 在 WSL 里即可看到 `/dev/ttyUSB*`（或 `/dev/ttyACM*`），开始串口调试。

## 工作原理

程序通过调用 `usbipd` 命令行实现功能，**usbipd 5.3** 的命令映射如下：

| 操作                 | 命令                                                  |
|----------------------|-------------------------------------------------------|
| 扫描                 | `usbipd state`（回退 `usbipd list`）                  |
| 绑定                 | `usbipd bind --busid <id> [--force]`                  |
| 解绑                 | `usbipd unbind --busid <id>`                          |
| 附加（默认发行版）   | `usbipd attach --wsl --busid <id>`                    |
| 附加（指定发行版）   | `usbipd attach --wsl <distro> --busid <id>`           |
| 附加（高级）         | 追加 `--host-ip <ip>` / `--auto-attach`               |
| 分离                 | `usbipd detach --busid <id>`                          |

> **注意：** usbipd 5.x 的 `attach` 仅支持 WSL，远程 `--address` 选项已移除。

## 项目结构

```
UsbipdTool/
├── app.py                  # 入口：检测 usbipd → 主窗口
├── core/                   # 核心层（不依赖 GUI，可单测）
│   ├── models.py           # UsbDevice / WslDistro
│   ├── parser.py           # state JSON / list 文本 / wsl 列表解析
│   ├── usbipd.py           # 命令封装、输出解码、is_admin
│   ├── actions.py          # bind/unbind/attach/detach/scan
│   └── config.py           # 配置读写
├── gui/                    # GUI 层
│   ├── main_window.py      # 主窗口
│   ├── attach_dialog.py    # 附加对话框
│   ├── worker.py           # QThread 后台执行
│   ├── i18n.py             # 轻量词典 i18n
│   └── theme.py            # 浅色/深色主题 + 调色板
├── resources/
│   ├── i18n/zh_CN.json     # 中文词典
│   ├── i18n/en_US.json     # 英文词典
│   ├── styles_light.qss    # 浅色样式
│   ├── styles_dark.qss     # 深色样式
│   └── icon.ico            # 图标
├── requirements.txt
├── UsbipdTool.spec         # PyInstaller 配置（uac_admin）
├── README.md
└── README_ZH.md
```

## 配置说明

配置保存在 `%APPDATA%\UsbipdTool\config.json`：

| 键                    | 类型   | 默认值 | 说明                                   |
|-----------------------|--------|--------|----------------------------------------|
| `language`            | string | `""`   | `""` = 跟随系统，`"zh_CN"`，`"en_US"`  |
| `theme`               | string | `""`   | `""` = 跟随系统，`"light"`，`"dark"`   |
| `force_bind_default`  | bool   | `false`| 「强制绑定」复选框默认状态             |
| `last_wsl_distro`     | string | `""`   | 记住上次使用的 WSL 发行版             |
| `last_host_ip`        | string | `""`   | 记住上次填写的主机 IP                 |
| `auto_attach_default` | bool   | `false`| 「自动重新附加」默认值                |

## 从源码构建

> 需要 Python 3.10+（已在 3.13 上测试）。Windows 下若 `python` 解析到 Microsoft
> Store 占位 stub，请改用真实解释器路径。

```powershell
# 1. 安装依赖
python -m pip install -r requirements.txt

# 2. 生成图标（可选，已提供脚本）
python _make_icon.py

# 3. 打包（单文件、无控制台、内嵌管理员清单）
python -m PyInstaller UsbipdTool.spec --noconfirm
```

产物：`dist\UsbipdTool.exe`（约 26 MB，单文件）。

## 已知问题

- **usbipd 5.x** 移除了 `usbipd wsl list` 子命令与远程 `--address` 选项，`attach` 现在只面向 WSL。
- 安装了 **USBPcap / hrdevmon** 过滤器驱动时，普通 `bind` 可能失败——请使用
  「强制绑定」（`--force`），程序会在失败时自动提示重试。
- 需要管理员权限；EXE 内嵌 `requireAdministrator` 清单（启动时弹一次 UAC）。

## 贡献指南

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。本项目遵循
[Contributor Covenant 行为准则](CODE_OF_CONDUCT.md)。

## 安全

如需报告安全漏洞，请参见 [SECURITY.md](SECURITY.md)。

## 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

## 致谢

- [usbipd-win](https://github.com/dorssel/usbipd-win) — 底层的 USB/IP 工具。
