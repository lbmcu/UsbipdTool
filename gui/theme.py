"""主题（浅色/深色）检测与应用。"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from core.models import STATE_ATTACHED, STATE_NOT_SHARED, STATE_SHARED

_current_theme = "light"


def system_dark() -> bool:
    """读取 Windows「应用模式」是否为深色。"""
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:  # noqa: BLE001
        return False


def effective_theme(pref: str) -> str:
    """根据用户偏好返回实际主题：light / dark。"""
    if pref in ("light", "dark"):
        return pref
    return "dark" if system_dark() else "light"


def current() -> str:
    return _current_theme


def _dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor("#1b1c20"))
    p.setColor(QPalette.WindowText, QColor("#e8eaed"))
    p.setColor(QPalette.Base, QColor("#222329"))
    p.setColor(QPalette.AlternateBase, QColor("#282a30"))
    p.setColor(QPalette.ToolTipBase, QColor("#2b2d33"))
    p.setColor(QPalette.ToolTipText, QColor("#e8eaed"))
    p.setColor(QPalette.Text, QColor("#e8eaed"))
    p.setColor(QPalette.PlaceholderText, QColor("#8a8f98"))
    p.setColor(QPalette.Button, QColor("#2f3136"))
    p.setColor(QPalette.ButtonText, QColor("#e8eaed"))
    p.setColor(QPalette.BrightText, QColor("#ff6b6b"))
    p.setColor(QPalette.Link, QColor("#7ab0ff"))
    p.setColor(QPalette.Highlight, QColor("#3d6ee0"))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor("#6b6e76"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#6b6e76"))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#6b6e76"))
    return p


def _light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor("#f5f6f8"))
    p.setColor(QPalette.WindowText, QColor("#1f2328"))
    p.setColor(QPalette.Base, QColor("#ffffff"))
    p.setColor(QPalette.AlternateBase, QColor("#fafbfc"))
    p.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    p.setColor(QPalette.ToolTipText, QColor("#1f2328"))
    p.setColor(QPalette.Text, QColor("#1f2328"))
    p.setColor(QPalette.PlaceholderText, QColor("#8a8f98"))
    p.setColor(QPalette.Button, QColor("#ffffff"))
    p.setColor(QPalette.ButtonText, QColor("#1f2328"))
    p.setColor(QPalette.BrightText, QColor("#c0392b"))
    p.setColor(QPalette.Link, QColor("#0969da"))
    p.setColor(QPalette.Highlight, QColor("#2f6fed"))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor("#9aa0a8"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#9aa0a8"))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#9aa0a8"))
    return p


def _resource_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "resources"
    return Path(__file__).resolve().parent.parent / "resources"


def load_qss(theme: str) -> str:
    name = "styles_dark.qss" if theme == "dark" else "styles_light.qss"
    path = _resource_dir() / name
    try:
        return path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


def apply_theme(app: QApplication, theme: str) -> None:
    """应用主题：Fusion 风格 + 调色板 + QSS。"""
    global _current_theme
    app.setStyle("Fusion")
    app.setPalette(_dark_palette() if theme == "dark" else _light_palette())
    app.setStyleSheet(load_qss(theme))
    _current_theme = theme


_STATE_COLORS = {
    "light": {
        STATE_NOT_SHARED: "#6b7280",
        STATE_SHARED: "#1a7f37",
        STATE_ATTACHED: "#0969da",
    },
    "dark": {
        STATE_NOT_SHARED: "#9ca3af",
        STATE_SHARED: "#3fb950",
        STATE_ATTACHED: "#58a6ff",
    },
}


def state_color(state: str, theme: str | None = None) -> str:
    t = theme or _current_theme
    table = _STATE_COLORS.get(t, _STATE_COLORS["light"])
    return table.get(state, "#808080")
