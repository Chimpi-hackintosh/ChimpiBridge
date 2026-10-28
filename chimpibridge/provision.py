"""Prepare a verified official Windows ADB package in the user's data folder."""
from __future__ import annotations

import hashlib
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from time import monotonic
from urllib.request import Request, urlopen

from .adb import AdbClient, BridgeError

# Versioned Google archive, checked against repository2-3.xml on 2026-10-28.
VERSION = "37.0.1"
ARCHIVE_URL = f"https://dl.google.com/android/repository/platform-tools_r{VERSION}-win.zip"
ARCHIVE_SIZE = 8044989
ARCHIVE_SHA256 = "45f4d63113e895ebde0c90f194099a4676b6ac653bd28d54314a9e022bbc1a99"
REQUIRED = ("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "NOTICE.txt", "source.properties")
MAX_UNPACKED = 160 * 1024 * 1024
DOWNLOAD_TIMEOUT = 90


def cached_adb(user_root: Path) -> Path:
    return user_root / "tools" / f"platform-tools-{VERSION}" / "platform-tools" / "adb.exe"


def _complete(path: Path) -> bool:
    return all((path.parent / name).is_file() for name in REQUIRED)


def _extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as package:
        members = package.infolist()
        names = set()
        size = 0
        for member in members:
            path = PurePosixPath(member.filename)
            canonical = member.filename.casefold().rstrip("/")
            mode = member.external_attr >> 16
            # Only the original platform-tools directory may be written.
            if (not path.parts or path.parts[0] != "platform-tools" or path.is_absolute()
                    or ".." in path.parts or "\\" in member.filename or ":" in member.filename
                    or any(part.endswith((".", " ")) for part in path.parts)
                    or stat.S_ISLNK(mode) or canonical in names):
                raise BridgeError("error.adb_package")
            names.add(canonical)
            size += member.file_size
        if len(members) > 2000 or size > MAX_UNPACKED:
            raise BridgeError("error.adb_package")
        package.extractall(destination)


def install_platform_tools(user_root: Path, *, opener=None, client_factory=AdbClient) -> Path:
    """Download at most once per call; never execute a shell or change system PATH."""
    if sys.platform != "win32":
        raise BridgeError("error.adb_auto_windows")
    target = cached_adb(user_root)
    if _complete(target):
        client_factory(target).version()
        return target
    try:
        target.parents[2].mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="adb-download-", dir=target.parents[2]) as temporary:
            staging = Path(temporary)
            archive = staging / "platform-tools.zip"
            request = Request(ARCHIVE_URL, headers={"User-Agent": "ChimpiBridge"})
            started, downloaded = monotonic(), 0
            digest = hashlib.sha256()
            with (opener or urlopen)(request, timeout=15) as response, archive.open("wb") as output:
                while chunk := response.read(64 * 1024):
                    downloaded += len(chunk)
                    if downloaded > ARCHIVE_SIZE or monotonic() - started > DOWNLOAD_TIMEOUT:
                        raise BridgeError("error.adb_download")
                    digest.update(chunk)
                    output.write(chunk)
            if downloaded != ARCHIVE_SIZE or digest.hexdigest() != ARCHIVE_SHA256:
                raise BridgeError("error.adb_integrity")
            extracted = staging / "verified"
            _extract(archive, extracted)
            staged_adb = extracted / "platform-tools" / "adb.exe"
            if not _complete(staged_adb):
                raise BridgeError("error.adb_package")
            # SHA-256 and complete-package checks precede any execution.
            client_factory(staged_adb).version()
            destination = target.parents[1]
            if destination.exists():
                if _complete(target):
                    # A second instance may have finished while this one downloaded.
                    client_factory(target).version()
                    return target
                # Preserve an incomplete old cache until the replacement is ready.
                destination.rename(staging / "previous")
            try:
                extracted.rename(destination)
            except OSError:
                # Another app instance may have completed the same first-run download.
                if not _complete(target):
                    previous = staging / "previous"
                    if previous.exists() and not destination.exists():
                        previous.rename(destination)
                    raise
            return target
    except BridgeError:
        raise
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise BridgeError("error.adb_package", str(exc)) from exc
    except OSError as exc:
        raise BridgeError("error.adb_download", str(exc)) from exc
