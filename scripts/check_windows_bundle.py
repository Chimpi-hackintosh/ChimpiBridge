"""Launch a real Windows or macOS frozen executable from another directory."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    executable = Path(sys.argv[1]).resolve()
    with executable.open("rb") as stream:
        magic = stream.read(4)
    expected = {b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}
    if not (magic[:2] == b"MZ" if sys.platform == "win32" else magic in expected):
        raise RuntimeError("A native executable is required")
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    with tempfile.TemporaryDirectory(prefix="chimpibridge-exe-check-") as directory:
        report = Path(directory) / "startup.json"
        download = "--download-adb" in sys.argv[2:]
        command = [str(executable), "--smoke-test", str(report)]
        if download:
            command.append("--smoke-download-adb")
        subprocess.run(command, cwd=directory, env=environment,
                       timeout=150 if download else 45, check=True)
        data = json.loads(report.read_text(encoding="utf-8"))
        if data.get("status") != "ok" or not data.get("adb_available"):
            raise RuntimeError(f"Frozen application startup check failed: {data}")
        print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
