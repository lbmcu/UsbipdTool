"""解析 usbipd / wsl 输出。"""
from __future__ import annotations

import json
import re

from core.models import UsbDevice, STATE_ATTACHED, STATE_SHARED, STATE_NOT_SHARED

_VID_RE = re.compile(r"VID_([0-9A-Fa-f]{4})")
_PID_RE = re.compile(r"PID_([0-9A-Fa-f]{4})")

# usbipd list 表格行：BUSID  VID:PID  描述(可含空格/逗号)  状态(行尾)
_LIST_ROW_RE = re.compile(
    r"^(?P<busid>\S+)\s+"
    r"(?P<vidpid>[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\s+"
    r"(?P<desc>.*?)\s+"
    r"(?P<state>Not shared|Shared|Attached)\s*$"
)


def _extract_vidpid(instance_id: str) -> tuple[str, str]:
    """从 InstanceId（如 USB\\VID_1A86&PID_55D3\\...）提取 VID/PID。"""
    vid_m = _VID_RE.search(instance_id or "")
    pid_m = _PID_RE.search(instance_id or "")
    vid = vid_m.group(1).lower() if vid_m else ""
    pid = pid_m.group(1).lower() if pid_m else ""
    return vid, pid


def parse_state_json(text: str) -> list[UsbDevice]:
    """解析 `usbipd state` 的 JSON 输出（usbipd 5.x 主数据源）。"""
    data = json.loads(text)
    devices: list[UsbDevice] = []
    for item in data.get("Devices", []) or []:
        busid = (item.get("BusId") or "").strip()
        if not busid:
            continue
        instance_id = item.get("InstanceId") or ""
        vid, pid = _extract_vidpid(instance_id)
        client_ip = (item.get("ClientIPAddress") or "").strip() or None
        persisted_guid = (item.get("PersistedGuid") or "").strip() or None
        if client_ip:
            state = STATE_ATTACHED
        elif persisted_guid:
            state = STATE_SHARED
        else:
            state = STATE_NOT_SHARED
        devices.append(
            UsbDevice(
                busid=busid,
                vid=vid,
                pid=pid,
                description=(item.get("Description") or "").strip(),
                state=state,
                client_ip=client_ip,
                instance_id=instance_id,
                persisted_guid=persisted_guid,
            )
        )
    return devices


def parse_list_text(text: str) -> list[UsbDevice]:
    """解析 `usbipd list` 文本输出（旧版本回退）。"""
    devices: list[UsbDevice] = []
    in_connected = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "Connected:":
            in_connected = True
            continue
        if stripped == "Persisted:":
            break
        if not in_connected or not stripped:
            continue
        if stripped.startswith("BUSID"):
            continue
        m = _LIST_ROW_RE.match(line.rstrip())
        if not m:
            continue
        vid, pid = m.group("vidpid").split(":")
        devices.append(
            UsbDevice(
                busid=m.group("busid"),
                vid=vid.lower(),
                pid=pid.lower(),
                description=m.group("desc").strip(),
                state=m.group("state"),
            )
        )
    return devices


def parse_wsl_distros_quiet(text: str) -> list[str]:
    """解析 `wsl.exe --list --quiet` 输出。"""
    names: list[str] = []
    for line in text.splitlines():
        name = line.strip().strip("\ufeff").strip()
        if not name:
            continue
        names.append(name)
    return names


def parse_wsl_default_distro(text: str) -> str | None:
    """从 `wsl.exe --list --verbose` 输出中找出默认发行版（行首带 *）。"""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("*"):
            parts = s.split()
            if len(parts) >= 2:
                return parts[1].strip()
    return None
