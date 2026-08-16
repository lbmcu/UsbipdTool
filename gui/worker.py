"""后台任务执行器。"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal


class TaskWorker(QThread):
    """在后台线程执行可调用对象，完成后发射结果。"""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:  # noqa: D102
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.succeeded.emit(result)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))
