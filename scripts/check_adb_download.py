"""Exercise the real Google download and hidden ADB launch on a Windows runner."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chimpibridge.adb import AdbClient
from chimpibridge.provision import install_platform_tools


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="chimpibridge-adb-check-") as directory:
        path = install_platform_tools(Path(directory))
        print(AdbClient(path).version())
        assert install_platform_tools(Path(directory)) == path
        print("Official ADB download, SHA-256, extraction, hidden launch and reuse: OK")


if __name__ == "__main__":
    main()
