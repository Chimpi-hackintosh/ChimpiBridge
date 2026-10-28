"""Build the real Windows bundle first, then create its NSIS installer.

Run on Windows x64 with Python 3.12 x64. Platform-Tools must be extracted
from Google's official archive; the full folder and its notices are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from chimpibridge import __version__


def nsis_escape(text: str) -> str:
    return text.replace("$", "$$").replace('"', '$\\"')


def uninstall_manifest(staging: Path, output: Path) -> None:
    """Delete only files shipped by us; leave all unrelated user files alone."""
    lines = ["; Generated from the actual staging directory"]
    for path in sorted(staging.rglob("*")):
        if path.is_file():
            relative = str(path.relative_to(staging)).replace("/", "\\")
            lines.append(f'Delete "$INSTDIR\\{nsis_escape(relative)}"')
    directories = [p for p in staging.rglob("*") if p.is_dir()]
    for path in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        relative = str(path.relative_to(staging)).replace("/", "\\")
        lines.append(f'RMDir "$INSTDIR\\{nsis_escape(relative)}"')
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_notices(staging: Path) -> None:
    destination = staging / "licenses"
    destination.mkdir(exist_ok=True)
    for name in ("PySide6_Essentials", "shiboken6", "PyInstaller"):
        distribution = metadata.distribution(name)
        for item in distribution.files or []:
            if any(part.lower() == "licenses" for part in item.parts):
                source = Path(distribution.locate_file(item))
                if source.is_file():
                    relative = Path(*item.parts[item.parts.index("licenses") + 1:]) if "licenses" in item.parts else Path(item.name)
                    target = destination / name / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copy2(python_license, destination / "Python-LICENSE.txt")


def find_nsis() -> str | None:
    found = shutil.which("makensis.exe")
    if found:
        return found
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variable)
        if base and (Path(base) / "NSIS" / "makensis.exe").is_file():
            return str(Path(base) / "NSIS" / "makensis.exe")
    return None


def build(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform-tools", type=Path, default=ROOT / "tools" / "platform-tools")
    parser.add_argument("--portable-only", action="store_true")
    args = parser.parse_args(argv)
    if sys.platform != "win32" or struct.calcsize("P") != 8 or platform.machine().upper() not in {"AMD64", "X86_64"}:
        parser.error("Build on Windows x64 using Python x64 / Execute no Windows x64 com Python x64")
    tools = args.platform_tools.resolve()
    required = ("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "NOTICE.txt", "source.properties")
    missing = [name for name in required if not (tools / name).is_file()]
    if missing:
        parser.error("Extract the complete official Platform-Tools ZIP to tools/platform-tools first / "
                     "Extraia o ZIP oficial completo em tools/platform-tools primeiro: " + ", ".join(missing))
    nsis = None if args.portable_only else find_nsis()
    if not args.portable_only and nsis is None:
        parser.error("Install NSIS 3 first, or use --portable-only / Instale o NSIS 3 ou use --portable-only")

    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_core.py"],
                   cwd=ROOT, check=True)
    build_dir, release_dir = ROOT / "build", ROOT / "release"
    build_dir.mkdir(exist_ok=True)
    release_dir.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
                    "--windowed", "--contents-directory", "lib", "--name", "ChimpiBridge",
                    "--hidden-import", "PySide6.QtSvg",
                    "--icon", str(ROOT / "assets" / "mark.ico"), "--distpath", str(ROOT / "dist"),
                    "--workpath", str(build_dir / "pyinstaller"), "--specpath", str(build_dir),
                    str(ROOT / "main.py")], cwd=ROOT, check=True)
    staging = ROOT / "dist" / "ChimpiBridge"
    for folder in ("assets", "locales"):
        shutil.copytree(ROOT / folder, staging / folder, dirs_exist_ok=True)
    for name in ("settings.default.json", "README.txt", "THIRD_PARTY_NOTICES.md", "LICENSE"):
        shutil.copy2(ROOT / name, staging / name)
    shutil.copytree(tools, staging / "tools" / "platform-tools", dirs_exist_ok=True)
    copy_notices(staging)
    if not (staging / "ChimpiBridge.exe").is_file():
        raise RuntimeError("Missing executable in staging")
    exposed = [str(p.relative_to(staging)) for p in staging.rglob("*") if p.suffix.lower() in {".py", ".pyw"}]
    if exposed:
        raise RuntimeError("Python source files in distribution: " + ", ".join(exposed))
    info = {"version": __version__, "built_at": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(), "target": "windows-x64",
            "packages": {name: metadata.version(name) for name in ("PySide6_Essentials", "shiboken6", "PyInstaller")},
            "adb_sha256": hashlib.sha256((tools / "adb.exe").read_bytes()).hexdigest()}
    (staging / "build-info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    archive = release_dir / f"ChimpiBridge-{__version__}-windows-x64-portable"
    shutil.make_archive(str(archive), "zip", root_dir=staging.parent, base_dir=staging.name)
    if nsis:
        manifest = build_dir / "uninstall-files.nsh"
        uninstall_manifest(staging, manifest)
        output = release_dir / f"ChimpiBridge-{__version__}-windows-x64-setup.exe"
        subprocess.run([nsis, f"/DSTAGING={staging}", f"/DOUTPUT={output}",
                        f"/DUNINSTALL_LIST={manifest}", str(ROOT / "installer" / "ChimpiBridge.nsi")],
                       cwd=ROOT, check=True)
        print(output)
    print(str(archive) + ".zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
