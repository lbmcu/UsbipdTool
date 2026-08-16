"""usbipd / wsl 命令封装与输出解码。"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

USBIPD_NAME = "usbipd"
WSL_NAME = "wsl.exe"

_KNOWN_USBIPD_PATHS = (
    Path(r"C:\Program Files\usbipd-win\usbipd.exe"),
    Path(r"C:\Program Files (x86)\usbipd-win\usbipd.exe"),
)


def is_admin() -> bool:
    """是否以管理员权限运行。"""
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def _decode(data: bytes) -> str:
    if not data:
        return ""
    # BOM 检测（wsl.exe 输出 UTF-16）
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    # 无 BOM 的 UTF-16 启发式：字节流中大量空字节
    if len(data) >= 4 and data.count(0) > len(data) // 4:
        try:
            return data.decode("utf-16-le", errors="replace")
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8", "gbk", "mbcs"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def error_text(self) -> str:
        return (self.stderr or self.stdout).strip()


def find_usbipd() -> str | None:
    exe = shutil.which(USBIPD_NAME)
    if exe:
        return exe
    for p in _KNOWN_USBIPD_PATHS:
        if p.is_file():
            return str(p)
    return None


def _resolve_wsl() -> str:
    return shutil.which(WSL_NAME) or WSL_NAME


def run_usbipd(args: list[str], timeout: int = 60) -> CommandResult:
    exe = find_usbipd() or USBIPD_NAME
    try:
        proc = subprocess.run([exe, *args], capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return CommandResult(-1, "", f"找不到 {USBIPD_NAME} 可执行文件。")
    except subprocess.TimeoutExpired:
        return CommandResult(-2, "", "命令执行超时。")
    return CommandResult(proc.returncode, _decode(proc.stdout), _decode(proc.stderr))


def run_wsl(args: list[str], timeout: int = 30) -> CommandResult:
    try:
        proc = subprocess.run([_resolve_wsl(), *args], capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return CommandResult(-1, "", "找不到 wsl.exe。")
    except subprocess.TimeoutExpired:
        return CommandResult(-2, "", "命令执行超时。")
    return CommandResult(proc.returncode, _decode(proc.stdout), _decode(proc.stderr))


def get_version() -> str | None:
    res = run_usbipd(["--version"], timeout=15)
    if res.ok:
        line = res.stdout.strip().splitlines()
        if line:
            v = line[0].strip()
            # 去掉 +Branch.master.Sha... 之类的构建后缀
            return v.split("+")[0][:40] if "+" in v else v[:40]
    return None
