"""Build a native macOS .app and archive it without losing symlinks or modes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import plistlib
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from chimpibridge import __author__, __version__
from chimpibridge.adb import AdbClient
from scripts.build_windows import copy_notices


def platform_tools(build: Path) -> Path:
    existing = Path(os.environ.get("ANDROID_HOME", str(build / "no-sdk"))) / "platform-tools"
    if (existing / "adb").is_file():
        return existing
    archive = build / "platform-tools-macos.zip"
    url = "https://dl.google.com/android/repository/platform-tools_r37.0.1-darwin.zip"
    with urllib.request.urlopen(url, timeout=30) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
    data = archive.read_bytes()
    if len(data) != 16110554 or hashlib.sha1(data).hexdigest() != "6ae73f4de6452dc57e62ec02b68eed92a4c21661":
        raise RuntimeError("Official macOS Platform-Tools archive checksum mismatch")
    destination = build / "android"
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            if not item.filename.startswith("platform-tools/") or ".." in Path(item.filename).parts:
                raise RuntimeError("Unexpected Platform-Tools archive path")
        package.extractall(destination)
        for item in package.infolist():
            mode = stat.S_IMODE(item.external_attr >> 16)
            if mode and not item.is_dir():
                (destination / item.filename).chmod(mode)
    return destination / "platform-tools"


def make_icon(build: Path) -> Path:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    application = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(ROOT / "assets" / "mark.svg"))
    folder = build / "mark.iconset"
    folder.mkdir(exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            suffix = "@2x" if scale == 2 else ""
            if not image.save(str(folder / f"icon_{size}x{size}{suffix}.png")):
                raise RuntimeError("Could not render the application icon")
    icon = build / "mark.icns"
    subprocess.run(["iconutil", "-c", "icns", str(folder), "-o", str(icon)], check=True)
    return icon


def main() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("Build this package on macOS")
    build, release = ROOT / "build", ROOT / "release"
    build.mkdir(exist_ok=True)
    release.mkdir(exist_ok=True)
    tools = platform_tools(build)
    for name in ("adb", "NOTICE.txt", "source.properties"):
        if not (tools / name).is_file():
            raise RuntimeError("Incomplete macOS Platform-Tools package")
    AdbClient(tools / "adb").version()
    icon = make_icon(build)
    arch = platform.machine()
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
                    "--windowed", "--name", "ChimpiBridge", "--hidden-import", "PySide6.QtSvg",
                    "--icon", str(icon), "--osx-bundle-identifier", "io.github.chimpi-hackintosh.chimpibridge",
                    "--target-arch", arch, "--distpath", str(ROOT / "dist"),
                    "--workpath", str(build / "pyinstaller"), "--specpath", str(build),
                    str(ROOT / "main.py")], cwd=ROOT, check=True)
    app = ROOT / "dist" / "ChimpiBridge.app"
    resources = app / "Contents" / "Resources"
    for folder in ("assets", "locales"):
        shutil.copytree(ROOT / folder, resources / folder, dirs_exist_ok=True)
    for name in ("settings.default.json", "README.txt", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, resources / name)
    shutil.copytree(tools, resources / "tools" / "platform-tools", dirs_exist_ok=True)
    copy_notices(resources)
    plist_path = app / "Contents" / "Info.plist"
    info = plistlib.loads(plist_path.read_bytes())
    info.update(CFBundleShortVersionString=__version__, CFBundleVersion=__version__,
                LSMinimumSystemVersion="14.4", NSHumanReadableCopyright=f"Copyright (c) 2026 {__author__}")
    plist_path.write_bytes(plistlib.dumps(info))
    (resources / "build-info.json").write_text(json.dumps({"version": __version__, "author": __author__,
        "target": f"macos-{arch}", "python": platform.python_version(), "source_commit": os.environ.get("GITHUB_SHA", "")}, indent=2))
    exposed = [str(p) for p in app.rglob("*") if p.is_file() and p.suffix.lower() in {".py", ".pyw"}]
    if exposed:
        raise RuntimeError("Python sources in application bundle: " + ", ".join(exposed))
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    executable = app / "Contents" / "MacOS" / "ChimpiBridge"
    subprocess.run([sys.executable, "scripts/check_windows_bundle.py", str(executable)], cwd=ROOT, check=True)
    label = "arm64" if arch == "arm64" else "x64"
    archive = release / f"ChimpiBridge-{__version__}-macos-{label}.zip"
    subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), str(archive)], check=True)
    restored = build / "archive-check"
    subprocess.run(["ditto", "-x", "-k", str(archive), str(restored)], check=True)
    restored_app = restored / "ChimpiBridge.app"
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(restored_app)], check=True)
    subprocess.run([sys.executable, "scripts/check_windows_bundle.py",
                    str(restored_app / "Contents" / "MacOS" / "ChimpiBridge")], cwd=ROOT, check=True)
    print(archive)


if __name__ == "__main__":
    main()
