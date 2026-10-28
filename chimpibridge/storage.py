"""External resources, per-user settings and bounded local operation history."""
from __future__ import annotations

import ctypes
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def app_root() -> Path:
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent.parent
    executable_dir = Path(sys.executable).resolve().parent
    if sys.platform == "darwin":
        return executable_dir.parent / "Resources"
    if (executable_dir / "assets" / "style.qss").is_file():
        return executable_dir
    return Path(getattr(sys, "_MEIPASS", executable_dir))


def user_data_dir() -> Path:
    if sys.platform == "win32":
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 28, None, 0, buffer) == 0:
            return Path(buffer.value) / "SnoopyOS Company" / "ChimpiBridge"
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "SnoopyOS Company" / "ChimpiBridge"


class Store:
    def __init__(self, root: Path | None = None, resource_root: Path | None = None):
        self.root = root or user_data_dir()
        self.resource_root = resource_root or app_root()
        defaults = self._load(self.resource_root / "settings.default.json", {})
        self.settings = {"language": "auto", "adb_path": "", **defaults}
        saved = self._load(self.root / "settings.json", {})
        for key in ("language", "adb_path"):
            if isinstance(saved.get(key), str):
                self.settings[key] = saved[key]
        rows = self._load(self.root / "history.json", [])
        self.history = [row for row in rows if isinstance(row, dict) and isinstance(row.get("key"), str)
                        and isinstance(row.get("params"), dict) and isinstance(row.get("time"), str)][-200:]

    @staticmethod
    def _load(path: Path, default):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, type(default)) else default
        except (OSError, ValueError):
            return default

    def _save(self, name: str, data) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / name
        temporary = self.root / (name + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)

    def save_settings(self) -> None:
        self._save("settings.json", self.settings)

    def add(self, key: str, **params) -> dict:
        row = {"time": datetime.now().astimezone().isoformat(timespec="seconds"),
               "key": key, "params": params}
        self.history = [*self.history, row][-200:]
        self._save("history.json", self.history)
        return row
