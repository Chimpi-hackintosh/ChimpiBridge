"""Attach tested packages to a maintainer-owned draft; never create a release."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from chimpibridge import __author__, __version__

REPO = os.environ.get("GITHUB_REPOSITORY", "Chimpi-hackintosh/ChimpiBridge")
PREFIX = f"repos/{REPO}"
RELEASE_ID = os.environ.get("TARGET_RELEASE_ID", "")
TAG = f"v{__version__}"


def api(path: str, method="GET", payload=None):
    command = ["gh", "api", "--method", method, path]
    if payload is not None:
        command.extend(["--input", "-"])
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"GitHub {method} {path}: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def draft():
    if not RELEASE_ID.isdecimal():
        raise RuntimeError("Supply the numeric ID of a draft created by the maintainer")
    data = api(f"{PREFIX}/releases/{RELEASE_ID}")
    if data["author"]["login"].casefold() != __author__.casefold() or not data["draft"]:
        raise RuntimeError("The destination must be an unpublished release created by Chimpi-hackintosh")
    return data


def prepare():
    draft()
    api(f"{PREFIX}/releases/{RELEASE_ID}", "PATCH", {
        "tag_name": f"{TAG}-publisher-{RELEASE_ID}", "target_commitish": os.environ["GITHUB_SHA"],
        "draft": True, "prerelease": True})
    print("Maintainer-owned draft ready; no release was created by the build token")


def upload():
    data = draft()
    packages = sorted(p for p in (ROOT / "release").glob(f"ChimpiBridge-{__version__}-*")
                      if p.suffix in {".zip", ".exe"})
    if not packages:
        raise RuntimeError("No desktop packages were generated")
    files = []
    for path in packages:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        checksum = path.with_name(path.name + ".sha256")
        checksum.write_text(f"{digest}  {path.name}\n", encoding="ascii")
        files.extend([str(path), str(checksum)])
    subprocess.run(["gh", "release", "upload", data["tag_name"], *files,
                    "--clobber", "--repo", REPO], check=True)
    print("Desktop packages attached to the maintainer's draft")


def finalize():
    data = draft()
    expected = {f"ChimpiBridge-{__version__}-{name}" for name in (
        "windows-x64-portable.zip", "windows-x64.exe", "macos-arm64.zip", "macos-x64.zip")}
    expected |= {name + ".sha256" for name in expected.copy()}
    uploaded = {a["name"] for a in data["assets"] if a["state"] == "uploaded" and a["size"] > 0}
    if not expected <= uploaded:
        raise RuntimeError("Missing release assets: " + ", ".join(sorted(expected - uploaded)))
    previous = api(f"{PREFIX}/releases/tags/{TAG}")
    if previous["id"] == int(RELEASE_ID):
        return
    if previous["author"]["login"] != "github-actions[bot]" or previous.get("immutable"):
        raise RuntimeError("Refusing to replace an unrelated or immutable release")
    old_ref = api(f"{PREFIX}/git/ref/tags/{TAG}")["object"]["sha"]
    backup_tag = f"{TAG}-automation-backup-{previous['id']}"
    build_source = data["target_commitish"]
    backup_body = (f"Publicação automática anterior preservada com seus arquivos originais\n\n"
                   f"Revisão original: https://github.com/{REPO}/commit/{old_ref}\n\n"
                   + previous.get("body", ""))
    moved = False
    try:
        # Keep the old publication, its exact tag revision and all its assets.
        api(f"{PREFIX}/releases/{previous['id']}", "PATCH", {
            "draft": True, "tag_name": backup_tag, "name": f"Backup da publicação automática {TAG}",
            "target_commitish": os.environ["GITHUB_SHA"], "body": backup_body})
        moved = True
        notes = (ROOT / ".github" / "release-notes-windows.md").read_text(encoding="utf-8")
        notes += f"\nCódigo-fonte dos pacotes: https://github.com/{REPO}/commit/{build_source}\n"
        api(f"{PREFIX}/releases/{RELEASE_ID}", "PATCH", {
            "tag_name": TAG, "target_commitish": os.environ["GITHUB_SHA"],
            "name": f"ChimpiBridge {__version__} — Windows e macOS", "body": notes,
            "draft": True, "prerelease": True})
        current = api(f"{PREFIX}/git/ref/tags/{TAG}")["object"]["sha"]
        if current != old_ref:
            raise RuntimeError("The version tag changed during packaging; refusing to overwrite it")
        # The previous revision remains reachable in main and in the backup notes.
        # No extra tag is created for the private draft.
        api(f"{PREFIX}/git/refs/tags/{TAG}", "PATCH", {"sha": os.environ["GITHUB_SHA"], "force": True})
    except Exception:
        if moved:
            api(f"{PREFIX}/releases/{RELEASE_ID}", "PATCH", {
                "tag_name": data["tag_name"], "target_commitish": os.environ["GITHUB_SHA"], "draft": True})
            api(f"{PREFIX}/releases/{previous['id']}", "PATCH", {
                "tag_name": TAG, "target_commitish": os.environ["GITHUB_SHA"],
                "name": previous["name"], "body": previous.get("body", ""), "draft": False})
        raise
    print("Ready for its owner to publish; previous release preserved as a private draft")


if __name__ == "__main__":
    {"prepare": prepare, "upload": upload, "finalize": finalize}[sys.argv[1]]()
