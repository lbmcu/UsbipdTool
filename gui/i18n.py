"""轻量 i18n：JSON 词典 + tr()。"""
from __future__ import annotations

import json
import locale
import sys
from pathlib import Path

_SUPPORTED = {"zh_CN", "en_US"}
_current_lang = "zh_CN"
_dict: dict[str, str] = {}


def resource_dir() -> Path:
    """i18n 资源目录（兼容 PyInstaller 打包后的解包目录）。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "resources" / "i18n"
    return Path(__file__).resolve().parent.parent / "resources" / "i18n"


def detect_system_lang() -> str:
    try:
        name = locale.getdefaultlocale()[0] or ""
    except Exception:  # noqa: BLE001
        name = ""
    name = (name or "").lower()
    return "zh_CN" if name.startswith("zh") else "en_US"


def load(lang: str) -> bool:
    global _dict, _current_lang
    if lang not in _SUPPORTED:
        lang = "zh_CN"
    path = resource_dir() / f"{lang}.json"
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        _dict = {str(k): str(v) for k, v in data.items()}
        _current_lang = lang
        return True
    except Exception:  # noqa: BLE001
        return False


def tr(key: str, **kwargs) -> str:
    s = _dict.get(key)
    if s is None:
        s = key
    if kwargs:
        try:
            s = s.format(**kwargs)
        except Exception:  # noqa: BLE001
            pass
    return s


def current_lang() -> str:
    return _current_lang
