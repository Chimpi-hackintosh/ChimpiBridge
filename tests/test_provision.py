"""Download and cache tests use local ZIP fixtures; no network or phone is accessed."""
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from chimpibridge.adb import BridgeError, resolve_adb
from chimpibridge import provision


def package(extra=None, missing=()):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name in provision.REQUIRED:
            if name not in missing:
                archive.writestr("platform-tools/" + name, b"test fixture")
        for name, value in (extra or {}).items():
            archive.writestr(name, value)
    return output.getvalue()


class ProvisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(patch.stopall)
        patch("chimpibridge.provision.sys.platform", "win32").start()
        self.client = Mock()
        self.client.version.return_value = "Android Debug Bridge version 1.0.41"
        self.factory = Mock(return_value=self.client)

    def install(self, data, **kwargs):
        opener = Mock(return_value=io.BytesIO(data))
        with patch.object(provision, "ARCHIVE_SIZE", len(data)), patch.object(
                provision, "ARCHIVE_SHA256", hashlib.sha256(data).hexdigest()):
            path = provision.install_platform_tools(self.root, opener=opener,
                                                    client_factory=self.factory, **kwargs)
        return path, opener

    def test_verified_download_reuses_complete_cache_without_network(self):
        path, opener = self.install(package())
        self.assertEqual(path, provision.cached_adb(self.root))
        self.assertTrue(all((path.parent / n).is_file() for n in provision.REQUIRED))
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, provision.ARCHIVE_URL)
        self.assertEqual(opener.call_args.kwargs["timeout"], 15)
        offline = Mock(side_effect=AssertionError("Must not download cached ADB"))
        self.assertEqual(provision.install_platform_tools(self.root, opener=offline,
                         client_factory=self.factory), path)
        offline.assert_not_called()

    def test_corrupt_archive_is_never_extracted_or_executed(self):
        data = package()
        with patch.object(provision, "ARCHIVE_SIZE", len(data)), self.assertRaises(BridgeError) as raised:
            provision.install_platform_tools(self.root, opener=lambda *a, **k: io.BytesIO(data),
                                             client_factory=self.factory)
        self.assertEqual(raised.exception.code, "error.adb_integrity")
        self.factory.assert_not_called()
        self.assertFalse(provision.cached_adb(self.root).exists())

    def test_truncated_and_oversized_downloads_do_not_install(self):
        for size, code in [(2, "error.adb_download"), (100000, "error.adb_integrity")]:
            with self.subTest(size=size), patch.object(provision, "ARCHIVE_SIZE", size):
                with self.assertRaises(BridgeError) as raised:
                    provision.install_platform_tools(self.root,
                        opener=lambda *a, **k: io.BytesIO(b"invalid"), client_factory=self.factory)
                self.assertEqual(raised.exception.code, code)
        self.factory.assert_not_called()

    def test_path_traversal_is_rejected_even_for_a_verified_zip(self):
        with self.assertRaises(BridgeError) as raised:
            self.install(package({"platform-tools/../../escape.exe": b"bad"}))
        self.assertEqual(raised.exception.code, "error.adb_package")
        self.assertFalse((self.root / "escape.exe").exists())
        self.factory.assert_not_called()

    def test_missing_dlls_cannot_be_installed(self):
        with self.assertRaises(BridgeError) as raised:
            self.install(package(missing=("AdbWinApi.dll",)))
        self.assertEqual(raised.exception.code, "error.adb_package")
        self.factory.assert_not_called()

    def test_network_failure_preserves_existing_incomplete_cache(self):
        old = provision.cached_adb(self.root)
        old.parent.mkdir(parents=True)
        old.write_bytes(b"existing")
        with self.assertRaises(BridgeError) as raised:
            provision.install_platform_tools(self.root,
                opener=Mock(side_effect=OSError("offline")), client_factory=self.factory)
        self.assertEqual(raised.exception.code, "error.adb_download")
        self.assertEqual(old.read_bytes(), b"existing")
        self.assertEqual(list(old.parents[2].glob("adb-download-*")), [])

    def test_invalid_executable_is_not_published_to_cache(self):
        self.client.version.side_effect = BridgeError("error.invalid_adb")
        with self.assertRaises(BridgeError):
            self.install(package())
        self.assertFalse(provision.cached_adb(self.root).exists())

    def test_resolver_finds_managed_cache_but_honors_explicit_choice(self):
        path, _ = self.install(package())
        with patch("shutil.which", return_value=None):
            self.assertEqual(resolve_adb("", self.root / "app", path), path)
            with self.assertRaises(BridgeError):
                resolve_adb(str(self.root / "missing.exe"), self.root / "app", path)

    def test_incomplete_bundle_allows_automatic_preparation(self):
        adb = self.root / "tools" / "platform-tools" / "adb.exe"
        adb.parent.mkdir(parents=True)
        adb.write_bytes(b"stub")
        with patch("shutil.which", return_value=None), self.assertRaises(BridgeError):
            resolve_adb("", self.root)

    def test_non_windows_does_not_download_windows_binaries(self):
        with patch("chimpibridge.provision.sys.platform", "linux"), self.assertRaises(BridgeError) as raised:
            provision.install_platform_tools(self.root)
        self.assertEqual(raised.exception.code, "error.adb_auto_windows")


if __name__ == "__main__":
    unittest.main()
