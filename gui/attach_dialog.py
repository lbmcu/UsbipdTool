"""附加设备对话框。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from core.models import UsbDevice, WslDistro
from gui import i18n


class AttachDialog(QDialog):
    def __init__(
        self,
        device: UsbDevice,
        distros: list[WslDistro],
        parent=None,
        last_distro: str = "",
        last_host_ip: str = "",
        auto_attach_default: bool = False,
    ):
        super().__init__(parent)
        self._device = device
        self.setWindowTitle(i18n.tr("attach_dialog.title"))
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)

        info = QLabel(i18n.tr("attach_dialog.info", busid=device.busid, desc=device.description))
        info.setWordWrap(True)
        layout.addWidget(info)

        group = QGroupBox(i18n.tr("attach_dialog.group_wsl"))
        form = QFormLayout(group)

        self.cb_default = QCheckBox(i18n.tr("attach_dialog.use_default"))
        self.cb_default.setChecked(True)
        form.addRow("", self.cb_default)

        self.cb_distro = QComboBox()
        self.cb_distro.setEditable(True)
        for d in distros:
            label = d.name
            if d.is_default:
                label += f"  ({i18n.tr('attach_dialog.default_mark')})"
            self.cb_distro.addItem(label, d.name)
        if last_distro:
            idx = self.cb_distro.findData(last_distro)
            if idx < 0 and last_distro.strip():
                self.cb_distro.addItem(last_distro, last_distro)
                idx = self.cb_distro.count() - 1
            if idx >= 0:
                self.cb_distro.setCurrentIndex(idx)
        form.addRow(i18n.tr("attach_dialog.distro"), self.cb_distro)

        self.cb_auto = QCheckBox(i18n.tr("attach_dialog.auto_attach"))
        self.cb_auto.setChecked(auto_attach_default)
        form.addRow("", self.cb_auto)

        self.ed_host_ip = QLineEdit()
        self.ed_host_ip.setPlaceholderText(i18n.tr("attach_dialog.host_ip_placeholder"))
        if last_host_ip:
            self.ed_host_ip.setText(last_host_ip)
        form.addRow(i18n.tr("attach_dialog.host_ip"), self.ed_host_ip)

        layout.addWidget(group)

        self.lbl_preview = QLabel()
        self.lbl_preview.setObjectName("previewLabel")
        self.lbl_preview.setWordWrap(True)
        layout.addWidget(self.lbl_preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(i18n.tr("common.attach"))
        buttons.button(QDialogButtonBox.Cancel).setText(i18n.tr("common.cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.cb_default.toggled.connect(self._on_toggled)
        self.cb_distro.currentTextChanged.connect(self._update_preview)
        self.cb_auto.toggled.connect(self._update_preview)
        self.ed_host_ip.textChanged.connect(self._update_preview)

        self._on_toggled()
        self._update_preview()

    def _on_toggled(self) -> None:
        self.cb_distro.setEnabled(not self.cb_default.isChecked())
        self._update_preview()

    def _update_preview(self) -> None:
        parts = ["usbipd", "attach", "--busid", self._device.busid]
        if self.cb_auto.isChecked():
            parts.append("--auto-attach")
        ip = self.ed_host_ip.text().strip()
        if ip:
            parts += ["--host-ip", ip]
        distro = self.distribution
        if distro:
            parts += ["--wsl", distro]
        else:
            parts.append("--wsl")
        self.lbl_preview.setText(i18n.tr("attach_dialog.preview", cmd=" ".join(parts)))

    @property
    def distribution(self) -> str | None:
        if self.cb_default.isChecked():
            return None
        return self.cb_distro.currentData() or self.cb_distro.currentText().strip() or None

    @property
    def host_ip(self) -> str:
        return self.ed_host_ip.text().strip()

    @property
    def auto_attach(self) -> bool:
        return self.cb_auto.isChecked()
