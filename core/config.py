"""配置读写（%APPDATA%\\UsbipdTool\\config.json）。"""
from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "UsbipdTool"

_DEFAULTS = {
    "language": "",  # "" 表示跟随系统
    "theme": "",  # "" = 跟随系统；"light" / "dark"
    "force_bind_default": False,
    "last_wsl_distro": "",
    "last_host_ip": "",
    "auto_attach_default": False,
}


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.json"


def load() -> dict:
    data = dict(_DEFAULTS)
    try:
        p = config_path()
        if p.is_file():
            with p.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception:  # noqa: BLE001
        pass
    return data


def save(data: dict) -> None:
    try:
        d = config_dir()
        d.mkdir(parents=True, exist_ok=True)
        with config_path().open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:  # noqa: BLE001
        pass
