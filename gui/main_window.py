"""主窗口。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core import actions, config as config_mod, usbipd
from core.models import (
    STATE_ATTACHED,
    STATE_NOT_SHARED,
    STATE_SHARED,
    UsbDevice,
)
from gui import i18n, theme
from gui.attach_dialog import AttachDialog
from gui.worker import TaskWorker

_COL_BUSID = 0
_COL_VIDPID = 1
_COL_DESC = 2
_COL_STATE = 3
_COL_ACTION = 4

_STATE_KEY = {
    STATE_NOT_SHARED: "state.not_shared",
    STATE_SHARED: "state.shared",
    STATE_ATTACHED: "state.attached",
}


class MainWindow(QMainWindow):
    def __init__(self, cfg: dict):
        super().__init__()
        self._cfg = cfg
        self._devices: list[UsbDevice] = []
        self._distros: list = []
        self._workers: list[TaskWorker] = []
        self._busy = False

        self._version = usbipd.get_version()
        self._is_admin = usbipd.is_admin()
        self._theme = theme.current()

        self._build_ui()
        self._apply_language()

        self._on_refresh()
        self._warm_distros()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setWindowTitle("UsbipdTool")
        self.resize(880, 560)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # 信息行
        self._info_label = QLabel()
        self._info_label.setObjectName("infoLabel")
        self._info_label.setWordWrap(True)
        root.addWidget(self._info_label)

        # 顶部工具条
        topbar = QHBoxLayout()
        topbar.setSpacing(8)

        self._lang_label = QLabel(i18n.tr("common.language") + ":")
        topbar.addWidget(self._lang_label)
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("中文", "zh_CN")
        self._lang_combo.addItem("English", "en_US")
        idx = self._lang_combo.findData(i18n.current_lang())
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        topbar.addWidget(self._lang_combo)

        self._theme_label = QLabel(i18n.tr("common.theme") + ":")
        topbar.addWidget(self._theme_label)
        self._theme_combo = QComboBox()
        self._theme_combo.addItem(i18n.tr("theme.system"), "")
        self._theme_combo.addItem(i18n.tr("theme.light"), "light")
        self._theme_combo.addItem(i18n.tr("theme.dark"), "dark")
        tidx = self._theme_combo.findData(self._cfg.get("theme", ""))
        if tidx >= 0:
            self._theme_combo.setCurrentIndex(tidx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        topbar.addWidget(self._theme_combo)

        self._btn_refresh = QPushButton(i18n.tr("common.refresh"))
        self._btn_refresh.setObjectName("btnRefresh")
        self._btn_refresh.clicked.connect(self._on_refresh)
        topbar.addWidget(self._btn_refresh)

        self._cb_force = QCheckBox(i18n.tr("common.force_bind"))
        self._cb_force.setChecked(bool(self._cfg.get("force_bind_default")))
        self._cb_force.setToolTip(i18n.tr("common.force_bind_tip"))
        self._cb_force.toggled.connect(self._on_force_toggled)
        topbar.addWidget(self._cb_force)

        topbar.addStretch(1)
        root.addLayout(topbar)

        # 设备表格
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            [
                i18n.tr("col.busid"),
                i18n.tr("col.vidpid"),
                i18n.tr("col.device"),
                i18n.tr("col.state"),
                i18n.tr("col.action"),
            ]
        )
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(_COL_BUSID, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(_COL_VIDPID, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(_COL_DESC, QHeaderView.Stretch)
        header.setSectionResizeMode(_COL_STATE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(_COL_ACTION, QHeaderView.Fixed)
        self._table.setColumnWidth(_COL_ACTION, 190)
        root.addWidget(self._table, 1)

        # 日志面板
        log_header = QHBoxLayout()
        self._log_title = QLabel(i18n.tr("log.title"))
        self._log_title.setStyleSheet("font-weight: bold;")
        log_header.addWidget(self._log_title)
        log_header.addStretch(1)
        self._btn_clear = QPushButton(i18n.tr("common.clear"))
        self._btn_clear.clicked.connect(self._log_view_clear)
        log_header.addWidget(self._btn_clear)
        root.addLayout(log_header)

        self._log_view = QPlainTextEdit()
        self._log_view.setObjectName("logView")
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(3000)
        root.addWidget(self._log_view, 1)

        self.setCentralWidget(central)

        self._status_label = QLabel(i18n.tr("common.ready"))
        self.statusBar().addWidget(self._status_label)

    def _apply_language(self) -> None:
        self.setWindowTitle(i18n.tr("app.title"))
        self._lang_label.setText(i18n.tr("common.language") + ":")
        self._theme_label.setText(i18n.tr("common.theme") + ":")
        self._refresh_theme_combo()
        if self._version:
            self._info_label.setText(
                i18n.tr("status.usbipd_ready", version=self._version)
                + "   |   "
                + i18n.tr("status.admin_yes" if self._is_admin else "status.admin_no")
            )
        else:
            self._info_label.setText(
                i18n.tr("status.usbipd_detected")
                + "   |   "
                + i18n.tr("status.admin_yes" if self._is_admin else "status.admin_no")
            )
        self._btn_refresh.setText(i18n.tr("common.refresh"))
        self._cb_force.setText(i18n.tr("common.force_bind"))
        self._cb_force.setToolTip(i18n.tr("common.force_bind_tip"))
        self._btn_clear.setText(i18n.tr("common.clear"))
        self._log_title.setText(i18n.tr("log.title"))
        self._table.setHorizontalHeaderLabels(
            [
                i18n.tr("col.busid"),
                i18n.tr("col.vidpid"),
                i18n.tr("col.device"),
                i18n.tr("col.state"),
                i18n.tr("col.action"),
            ]
        )
        if self._busy:
            self._status_label.setText(i18n.tr("common.scanning"))
        elif not self._devices:
            self._status_label.setText(i18n.tr("status.no_devices"))
        else:
            self._status_label.setText(i18n.tr("common.ready"))

    # ------------------------------------------------------------- 扫描/显示
    def _on_refresh(self) -> None:
        if self._busy:
            return
        self._status_label.setText(i18n.tr("common.scanning"))
        self._start_worker(actions.scan_devices, self._on_scan_done)

    def _on_scan_done(self, result) -> None:
        devices, warning = result
        self._devices = devices
        self._populate()
        if warning:
            self._log("[warn] " + warning)
        self._status_label.setText(
            i18n.tr("status.no_devices") if not devices else i18n.tr("common.ready")
        )

    def _populate(self) -> None:
        self._table.setRowCount(0)
        for dev in self._devices:
            r = self._table.rowCount()
            self._table.insertRow(r)

            it = QTableWidgetItem(dev.busid)
            self._table.setItem(r, _COL_BUSID, it)

            it = QTableWidgetItem(dev.vidpid or "-")
            self._table.setItem(r, _COL_VIDPID, it)

            desc = dev.description or dev.instance_id or "-"
            it = QTableWidgetItem(desc)
            it.setToolTip(desc)
            self._table.setItem(r, _COL_DESC, it)

            state_text = i18n.tr(_STATE_KEY.get(dev.state, "state.not_shared"))
            if dev.is_attached and dev.client_ip:
                state_text += f" ({dev.client_ip})"
            it = QTableWidgetItem(state_text)
            it.setForeground(QColor(theme.state_color(dev.state, self._theme)))
            self._table.setItem(r, _COL_STATE, it)

            self._table.setCellWidget(r, _COL_ACTION, self._make_action_widget(dev))

    def _make_action_widget(self, dev: UsbDevice) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)

        def add(text: str, slot, obj_name: str = "") -> None:
            b = QPushButton(text)
            b.setCursor(Qt.PointingHandCursor)
            if obj_name:
                b.setObjectName(obj_name)
            b.clicked.connect(slot)
            lay.addWidget(b)

        busid = dev.busid
        if dev.is_not_shared:
            add(i18n.tr("btn.bind"), lambda _=False, b=busid: self._on_bind(b), "btnBind")
        elif dev.is_shared:
            add(i18n.tr("btn.attach"), lambda _=False, b=busid: self._on_attach(b), "btnAttach")
            add(i18n.tr("btn.unbind"), lambda _=False, b=busid: self._on_unbind(b), "btnUnbind")
        elif dev.is_attached:
            add(i18n.tr("btn.detach"), lambda _=False, b=busid: self._on_detach(b), "btnDetach")
            add(i18n.tr("btn.unbind"), lambda _=False, b=busid: self._on_unbind(b), "btnUnbind")
        lay.addStretch(1)
        return w

    # ------------------------------------------------------------- 操作
    def _on_bind(self, busid: str) -> None:
        if self._busy:
            return
        self._do_bind(busid, self._cb_force.isChecked())

    def _do_bind(self, busid: str, force: bool) -> None:
        cmd = f"usbipd bind --busid {busid}" + (" --force" if force else "")
        self._start_worker(
            lambda: actions.bind(busid, force=force),
            lambda res: self._after_bind(res, busid, force),
            cmd_text=cmd,
        )

    def _after_bind(self, res, busid: str, force: bool) -> None:
        self._log_output(res)
        if res.ok:
            self._log(i18n.tr("msg.bind_ok", busid=busid))
            self._on_refresh()
            return
        err = res.error_text.lower()
        if not force and any(k in err for k in ("incompatible", "--force", "hrdevmon", "usbpcap")):
            if self._ask_yes_no(i18n.tr("msg.bind_force_hint")):
                self._do_bind(busid, True)
            return
        self._warn(i18n.tr("msg.cmd_failed", code=res.returncode, err=res.error_text))

    def _on_attach(self, busid: str) -> None:
        if self._busy:
            return
        dev = self._find(busid)
        if dev is None:
            return
        self._ensure_distros()
        dlg = AttachDialog(
            dev,
            self._distros,
            self,
            last_distro=self._cfg.get("last_wsl_distro", ""),
            last_host_ip=self._cfg.get("last_host_ip", ""),
            auto_attach_default=bool(self._cfg.get("auto_attach_default")),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        distro = dlg.distribution
        host_ip = dlg.host_ip
        auto = dlg.auto_attach

        self._cfg["last_wsl_distro"] = distro or ""
        self._cfg["last_host_ip"] = host_ip
        self._cfg["auto_attach_default"] = auto
        config_mod.save(self._cfg)

        parts = ["usbipd", "attach", "--busid", busid]
        if auto:
            parts.append("--auto-attach")
        if host_ip:
            parts += ["--host-ip", host_ip]
        if distro:
            parts += ["--wsl", distro]
        else:
            parts.append("--wsl")

        self._start_worker(
            lambda: actions.attach_wsl(busid, distro, host_ip, auto),
            lambda res: self._after_attach(res, busid),
            cmd_text=" ".join(parts),
        )

    def _after_attach(self, res, busid: str) -> None:
        self._log_output(res)
        if res.ok:
            self._log(i18n.tr("msg.attach_ok", busid=busid))
            self._on_refresh()
        else:
            self._warn(i18n.tr("msg.cmd_failed", code=res.returncode, err=res.error_text))

    def _on_unbind(self, busid: str) -> None:
        if self._busy:
            return
        if not self._ask_yes_no(i18n.tr("msg.unbind_confirm", busid=busid)):
            return
        self._start_worker(
            lambda: actions.unbind(busid),
            lambda res: self._after_unbind(res, busid),
            cmd_text=f"usbipd unbind --busid {busid}",
        )

    def _after_unbind(self, res, busid: str) -> None:
        self._log_output(res)
        if res.ok:
            self._log(i18n.tr("msg.unbind_ok", busid=busid))
            self._on_refresh()
        else:
            self._warn(i18n.tr("msg.cmd_failed", code=res.returncode, err=res.error_text))

    def _on_detach(self, busid: str) -> None:
        if self._busy:
            return
        if not self._ask_yes_no(i18n.tr("msg.detach_confirm", busid=busid)):
            return
        self._start_worker(
            lambda: actions.detach(busid),
            lambda res: self._after_detach(res, busid),
            cmd_text=f"usbipd detach --busid {busid}",
        )

    def _after_detach(self, res, busid: str) -> None:
        self._log_output(res)
        if res.ok:
            self._log(i18n.tr("msg.detach_ok", busid=busid))
            self._on_refresh()
        else:
            self._warn(i18n.tr("msg.cmd_failed", code=res.returncode, err=res.error_text))

    # ------------------------------------------------------------- 工具
    def _find(self, busid: str) -> UsbDevice | None:
        return next((d for d in self._devices if d.busid == busid), None)

    def _ensure_distros(self) -> None:
        if self._distros:
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self._distros = actions.list_wsl_distros()
        finally:
            QApplication.restoreOverrideCursor()

    def _warm_distros(self) -> None:
        w = TaskWorker(actions.list_wsl_distros)

        def _done(res):
            self._distros = res or []
            self._workers = [x for x in self._workers if x is not w]

        w.succeeded.connect(_done)
        w.failed.connect(lambda _e: self._workers.remove(w) if w in self._workers else None)
        w.finished.connect(w.deleteLater)
        self._workers.append(w)
        w.start()

    def _start_worker(self, fn, on_success, cmd_text: str = "") -> None:
        if cmd_text:
            self._log("> " + cmd_text)
        self._set_busy(True)
        w = TaskWorker(fn)

        def _done(res):
            self._set_busy(False)
            if w in self._workers:
                self._workers.remove(w)
            on_success(res)

        def _fail(err):
            self._set_busy(False)
            if w in self._workers:
                self._workers.remove(w)
            self._log(i18n.tr("msg.op_failed") + ": " + err)
            self._warn(err)

        w.succeeded.connect(_done)
        w.failed.connect(_fail)
        w.finished.connect(w.deleteLater)
        self._workers.append(w)
        w.start()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def _ask_yes_no(self, text: str) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle("UsbipdTool")
        box.setIcon(QMessageBox.Question)
        box.setText(text)
        yes = box.addButton(i18n.tr("common.yes"), QMessageBox.YesRole)
        box.addButton(i18n.tr("common.no"), QMessageBox.NoRole)
        box.exec()
        return box.clickedButton() is yes

    def _warn(self, text: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("UsbipdTool")
        box.setIcon(QMessageBox.Warning)
        box.setText(text)
        box.addButton(i18n.tr("common.ok"), QMessageBox.AcceptRole)
        box.exec()

    def _log(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_view.appendPlainText(f"[{ts}] {text}")

    def _log_output(self, res) -> None:
        for line in res.stdout.splitlines():
            if line.strip():
                self._log(line)
        for line in res.stderr.splitlines():
            if line.strip():
                self._log("[stderr] " + line)

    def _log_view_clear(self) -> None:
        self._log_view.clear()

    # ------------------------------------------------------------- 事件
    def _on_lang_changed(self, idx: int) -> None:
        lang = self._lang_combo.itemData(idx)
        if not lang or lang == i18n.current_lang():
            return
        i18n.load(lang)
        self._cfg["language"] = lang
        config_mod.save(self._cfg)
        self._apply_language()
        self._populate()

    def _refresh_theme_combo(self) -> None:
        self._theme_combo.blockSignals(True)
        self._theme_combo.setItemText(0, i18n.tr("theme.system"))
        self._theme_combo.setItemText(1, i18n.tr("theme.light"))
        self._theme_combo.setItemText(2, i18n.tr("theme.dark"))
        self._theme_combo.blockSignals(False)

    def _on_theme_changed(self, idx: int) -> None:
        pref = self._theme_combo.itemData(idx)
        if pref is None:
            return
        self._cfg["theme"] = pref
        config_mod.save(self._cfg)
        self._apply_theme(theme.effective_theme(pref))

    def _apply_theme(self, theme_name: str) -> None:
        self._theme = theme_name
        theme.apply_theme(QApplication.instance(), theme_name)
        self._populate()

    def _on_force_toggled(self, checked: bool) -> None:
        self._cfg["force_bind_default"] = bool(checked)
        config_mod.save(self._cfg)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: D102
        for w in self._workers:
            if w.isRunning():
                w.wait(2000)
        event.accept()
