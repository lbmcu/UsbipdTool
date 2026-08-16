"""数据模型。"""
from __future__ import annotations

from dataclasses import dataclass

STATE_NOT_SHARED = "Not shared"
STATE_SHARED = "Shared"
STATE_ATTACHED = "Attached"


@dataclass
class UsbDevice:
    busid: str
    vid: str
    pid: str
    description: str
    state: str
    client_ip: str | None = None
    instance_id: str | None = None
    persisted_guid: str | None = None

    @property
    def vidpid(self) -> str:
        return f"{self.vid}:{self.pid}"

    @property
    def is_not_shared(self) -> bool:
        return self.state == STATE_NOT_SHARED

    @property
    def is_shared(self) -> bool:
        return self.state == STATE_SHARED

    @property
    def is_attached(self) -> bool:
        return self.state == STATE_ATTACHED


@dataclass
class WslDistro:
    name: str
    is_default: bool = False
