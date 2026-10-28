"""Launch the actual frozen Windows EXE from another working directory."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    executable = Path(sys.argv[1]).resolve()
    if not executable.is_file() or executable.read_bytes()[:2] != b"MZ":
        raise RuntimeError("A real Windows PE executable is required")
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    with tempfile.TemporaryDirectory(prefix="chimpibridge-exe-check-") as directory:
        report = Path(directory) / "startup.json"
        subprocess.run([str(executable), "--smoke-test", str(report)], cwd=directory,
                       env=environment, timeout=45, check=True)
        data = json.loads(report.read_text(encoding="utf-8"))
        if data.get("status") != "ok" or not data.get("adb_bundled"):
            raise RuntimeError(f"Frozen application startup check failed: {data}")
        print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
