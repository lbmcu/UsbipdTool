"""UsbipdTool 入口。"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from core import config, usbipd
from gui import i18n, theme
from gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("UsbipdTool")
    app.setOrganizationName("UsbipdTool")

    cfg = config.load()
    lang = cfg.get("language") or i18n.detect_system_lang()
    i18n.load(lang)
    theme.apply_theme(app, theme.effective_theme(cfg.get("theme", "")))

    if not usbipd.find_usbipd():
        box = QMessageBox()
        box.setWindowTitle("UsbipdTool")
        box.setIcon(QMessageBox.Critical)
        box.setText(i18n.tr("error.usbipd_not_found"))
        box.addButton(i18n.tr("common.ok"), QMessageBox.AcceptRole)
        box.exec()
        return 1

    win = MainWindow(cfg)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
