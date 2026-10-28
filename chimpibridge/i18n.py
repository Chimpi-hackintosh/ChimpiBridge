"""Use Windows display languages, with an explicit saved override first."""
from __future__ import annotations

import ctypes
import json
import locale
import os
import sys
from pathlib import Path


def display_languages() -> list[str]:
    if sys.platform == "win32":
        try:
            count, size = ctypes.c_ulong(), ctypes.c_ulong()
            function = ctypes.windll.kernel32.GetUserPreferredUILanguages
            if function(8, ctypes.byref(count), None, ctypes.byref(size)) and size.value:
                buffer = ctypes.create_unicode_buffer(size.value)
                if function(8, ctypes.byref(count), buffer, ctypes.byref(size)):
                    return [part for part in buffer[:size.value].split("\0") if part]
        except (AttributeError, OSError):
            pass
        return [locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "en")]
    if sys.platform == "darwin":
        from PySide6.QtCore import QLocale
        return QLocale.system().uiLanguages()
    return [*os.environ.get("LANGUAGE", "").split(":"), locale.getlocale()[0] or "en"]


def choose_language(override: str, candidates: list[str]) -> str:
    mapping = {"en": "en", "pt": "pt-BR"}
    for candidate in ([override] if override != "auto" else candidates):
        normalized = candidate.replace("_", "-").split(".")[0]
        if normalized in ("pt-BR", "en"):
            return normalized
        base = normalized.lower().split("-")[0]
        if base in mapping:
            return mapping[base]
    return "en"


class I18n:
    def __init__(self, root: Path, override: str = "auto", candidates: list[str] | None = None):
        self.language = choose_language(override, candidates if candidates is not None else display_languages())
        folder = root / "locales"
        self.base = json.loads((folder / "en.json").read_text(encoding="utf-8"))
        self.messages = json.loads((folder / f"{self.language}.json").read_text(encoding="utf-8"))

    def __call__(self, key: str, **params) -> str:
        return self.messages.get(key, self.base.get(key, key)).format(**params)
