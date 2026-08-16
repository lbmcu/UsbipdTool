"""高层操作，封装 usbipd 子命令。"""
from __future__ import annotations

from core import usbipd
from core.models import UsbDevice, WslDistro
from core.parser import (
    parse_list_text,
    parse_state_json,
    parse_wsl_default_distro,
    parse_wsl_distros_quiet,
)


def scan_devices() -> tuple[list[UsbDevice], str | None]:
    """扫描设备。优先 `usbipd state`（JSON），回退 `usbipd list`。

    返回 (设备列表, 警告文本)。警告文本通常是 stderr 里的过滤器警告。
    """
    res = usbipd.run_usbipd(["state"], timeout=30)
    if res.ok:
        try:
            return parse_state_json(res.stdout), (res.stderr.strip() or None)
        except Exception:  # noqa: BLE001
            # JSON 解析失败则回退到 list 文本解析
            pass

    res2 = usbipd.run_usbipd(["list"], timeout=30)
    if res2.ok:
        return parse_list_text(res2.stdout), (res2.stderr.strip() or None)
    return [], (res2.error_text or "扫描失败")


def list_wsl_distros() -> list[WslDistro]:
    """列出 WSL 发行版，并标记默认发行版。失败时返回空列表。"""
    default_name: str | None = None
    verbose = usbipd.run_wsl(["--list", "--verbose"], timeout=30)
    if verbose.ok:
        default_name = parse_wsl_default_distro(verbose.stdout)

    quiet = usbipd.run_wsl(["--list", "--quiet"], timeout=30)
    names = parse_wsl_distros_quiet(quiet.stdout) if quiet.ok else []
    return [WslDistro(name=n, is_default=(n == default_name)) for n in names]


def bind(busid: str, force: bool = False) -> usbipd.CommandResult:
    args = ["bind", "--busid", busid]
    if force:
        args.append("--force")
    return usbipd.run_usbipd(args)


def unbind(busid: str) -> usbipd.CommandResult:
    return usbipd.run_usbipd(["unbind", "--busid", busid])


def attach_wsl(
    busid: str,
    distribution: str | None = None,
    host_ip: str | None = None,
    auto_attach: bool = False,
) -> usbipd.CommandResult:
    args = ["attach", "--busid", busid]
    if auto_attach:
        args.append("--auto-attach")
    if host_ip:
        args += ["--host-ip", host_ip]
    if distribution:
        args += ["--wsl", distribution]
    else:
        args.append("--wsl")
    return usbipd.run_usbipd(args)


def detach(busid: str) -> usbipd.CommandResult:
    return usbipd.run_usbipd(["detach", "--busid", busid])
