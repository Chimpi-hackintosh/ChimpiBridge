"""ADB adapter. Only two restart destinations are exposed in version 0.1.

No shell interpolation, flashing, data erasure, root or bootloader unlocking.
Every device command explicitly includes the selected serial number.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable


class BridgeError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code, self.detail = code, detail


@dataclass(frozen=True)
class Device:
    serial: str
    state: str
    model: str = ""
    product: str = ""
    transport_id: str = ""

    @property
    def ready(self) -> bool:
        return self.state in ("device", "recovery")


def parse_devices(output: str) -> list[Device]:
    devices = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith(("List of devices", "*", "adb:")):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        # ADB prints "no permissions (user ...)", with a space in this state.
        state = "no_permissions" if fields[1:3] == ["no", "permissions"] else fields[1]
        if state not in {"device", "recovery", "unauthorized", "offline", "sideload",
                         "bootloader", "no_permissions", "host", "connecting",
                         "authorizing", "rescue", "detached"}:
            state = "unknown"
        extra = dict(field.split(":", 1) for field in fields[2:] if ":" in field)
        devices.append(Device(fields[0], state, extra.get("model", "").replace("_", " "),
                              extra.get("product", ""), extra.get("transport_id", "")))
    return devices


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def run_process(argv: list[str], timeout: float) -> Result:
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, shell=False, stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return Result(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        raise BridgeError("error.timeout") from exc
    except OSError as exc:
        raise BridgeError("error.execute", str(exc)) from exc


def resolve_adb(configured: str, root: Path) -> Path:
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            raise BridgeError("error.adb_missing")
        return path.resolve()
    name = "adb.exe" if sys.platform == "win32" else "adb"
    bundled = root / "tools" / "platform-tools" / name
    if bundled.is_file():
        return bundled
    found = shutil.which(name)
    if found:
        return Path(found).resolve()
    raise BridgeError("error.adb_missing")


class Target(str, Enum):
    SYSTEM = "system"
    RECOVERY = "recovery"


@dataclass(frozen=True)
class Observation:
    device: Device
    mode: str
    boot_id: str = ""
    boot_completed: bool = False


@dataclass(frozen=True)
class RebootReceipt:
    serial: str
    target: Target
    before: Observation


class AdbClient:
    def __init__(self, path: Path, runner: Callable = run_process):
        self.path, self.runner = path, runner

    def _run(self, *args: str, timeout: float = 8) -> Result:
        result = self.runner([str(self.path), *args], timeout)
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()[-3000:]
            lowered = detail.lower()
            code = "error.command"
            if "unauthorized" in lowered:
                code = "error.unauthorized"
            elif "offline" in lowered:
                code = "error.offline"
            elif "not found" in lowered or "no devices" in lowered:
                code = "error.disconnected"
            raise BridgeError(code, detail)
        return result

    def version(self) -> str:
        result = self._run("version")
        if "Android Debug Bridge" not in result.stdout:
            raise BridgeError("error.invalid_adb")
        return result.stdout.strip()

    def scan(self) -> list[Device]:
        return parse_devices(self._run("devices", "-l").stdout)

    def _read(self, serial: str, *args: str) -> str:
        try:
            return self._run("-s", serial, "shell", *args, timeout=3).stdout.strip()
        except BridgeError:
            # Some recoveries restrict shell or omit these properties.
            # Missing evidence must never be converted into success.
            return ""

    def observe(self, device: Device) -> Observation:
        if not device.ready:
            return Observation(device, device.state)
        mode = "recovery" if device.state == "recovery" else "adb"
        if device.state == "device":
            bootmode = self._read(device.serial, "getprop", "ro.bootmode")
            if bootmode.lower() == "recovery":
                mode = "recovery"
        boot_id = self._read(device.serial, "cat", "/proc/sys/kernel/random/boot_id")
        # Avoid treating shell error text or an empty string as a unique ID.
        import re
        if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", boot_id):
            boot_id = ""
        completed = mode == "adb" and self._read(device.serial, "getprop", "sys.boot_completed") == "1"
        return Observation(device, mode, boot_id, completed)

    def reboot(self, serial: str, target: Target) -> RebootReceipt:
        if not isinstance(target, Target):
            raise BridgeError("error.unsupported")
        # Recheck authorization and presence immediately before targeting a device.
        current = next((d for d in self.scan() if d.serial == serial), None)
        if current is None:
            raise BridgeError("error.disconnected")
        if not current.ready:
            code = {"unauthorized": "error.unauthorized", "offline": "error.offline"}.get(
                current.state, "error.unavailable")
            raise BridgeError(code)
        before = self.observe(current)
        args = ["-s", serial, "reboot"]
        if target == Target.RECOVERY:
            args.append("recovery")
        self._run(*args, timeout=12)
        return RebootReceipt(serial, target, before)


@dataclass
class Transition:
    """Separate 'command accepted' from confirmed observation of the target."""
    receipt: RebootReceipt
    started: float
    timeout: float = 90.0
    saw_disconnect: bool = False

    def update(self, devices: list[Device], observation: Observation | None, now: float) -> str:
        matching = next((d for d in devices if d.serial == self.receipt.serial), None)
        if matching is None:
            self.saw_disconnect = True
        elif observation is not None and observation.device.serial == self.receipt.serial:
            changed_id = bool(self.receipt.before.boot_id and observation.boot_id and
                              self.receipt.before.boot_id != observation.boot_id)
            if matching.ready:
                if self.receipt.target == Target.RECOVERY:
                    fresh = self.receipt.before.mode != "recovery" or changed_id or self.saw_disconnect
                    if observation.mode == "recovery" and fresh:
                        return "confirmed"
                elif (observation.mode == "adb" and observation.boot_completed and
                      (changed_id or self.saw_disconnect or self.receipt.before.mode == "recovery")):
                    return "confirmed"
        return "unconfirmed" if now - self.started >= self.timeout else "waiting"
