from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chimpibridge.adb import (AdbClient, BridgeError, Device, Observation, RebootReceipt,
    Result, Target, Transition, parse_devices, resolve_adb, run_process)
from chimpibridge.i18n import I18n, choose_language
from chimpibridge.storage import Store, app_root
from scripts.build_windows import uninstall_manifest

ROOT = Path(__file__).resolve().parent.parent
BOOT_A = "12345678-1234-1234-1234-123456789abc"
BOOT_B = "87654321-4321-4321-4321-cba987654321"


class FakeRunner:
    def __init__(self):
        self.calls = []
        self.listing = "List of devices attached\nalpha device model:Galaxy_J4 transport_id:1\nbeta device model:Other transport_id:2\n"
        self.reboot_result = Result(0)

    def __call__(self, argv, timeout):
        args = argv[1:]
        self.calls.append(args)
        if args == ["devices", "-l"]:
            return Result(0, self.listing)
        if "reboot" in args:
            return self.reboot_result
        if args[-2:] == ["getprop", "ro.bootmode"]:
            return Result(0, "normal\n")
        if args[-2:] == ["getprop", "sys.boot_completed"]:
            return Result(0, "1\n")
        if "cat" in args:
            return Result(0, BOOT_A + "\n")
        if args == ["version"]:
            return Result(0, "Android Debug Bridge version 1.0.41")
        return Result(1, stderr="unexpected command")


class AdbTests(unittest.TestCase):
    def test_parse_mixed_states_and_permissions(self):
        output = "* daemon started successfully\nList of devices attached\nA device product:p model:SM_J410G transport_id:1\nB unauthorized\nC offline\nD no permissions (user in group plugdev)\nE sideload\nF recovery\nG new_state\n"
        rows = parse_devices(output)
        self.assertEqual([d.state for d in rows], ["device", "unauthorized", "offline", "no_permissions", "sideload", "recovery", "unknown"])
        self.assertEqual(rows[0].model, "SM J410G")
        self.assertEqual(rows[0].transport_id, "1")

    def test_restart_targets_only_selected_device(self):
        runner = FakeRunner()
        receipt = AdbClient(Path("adb"), runner).reboot("beta", Target.RECOVERY)
        self.assertEqual(receipt.serial, "beta")
        self.assertIn(["-s", "beta", "reboot", "recovery"], runner.calls)
        for call in runner.calls:
            if call != ["devices", "-l"]:
                self.assertEqual(call[:2], ["-s", "beta"])

    def test_normal_restart_does_not_send_erase_or_flash(self):
        runner = FakeRunner()
        AdbClient(Path("adb"), runner).reboot("alpha", Target.SYSTEM)
        self.assertEqual(runner.calls[-1], ["-s", "alpha", "reboot"])

    def test_revoked_authorization_prevents_restart(self):
        runner = FakeRunner()
        runner.listing = "List of devices attached\nalpha unauthorized\n"
        with self.assertRaises(BridgeError) as raised:
            AdbClient(Path("adb"), runner).reboot("alpha", Target.RECOVERY)
        self.assertEqual(raised.exception.code, "error.unauthorized")
        self.assertFalse(any("reboot" in call for call in runner.calls))

    def test_disconnected_device_does_not_fall_back_to_other_phone(self):
        runner = FakeRunner()
        with self.assertRaises(BridgeError) as raised:
            AdbClient(Path("adb"), runner).reboot("missing", Target.SYSTEM)
        self.assertEqual(raised.exception.code, "error.disconnected")
        self.assertFalse(any("reboot" in call for call in runner.calls))

    def test_sideload_does_not_offer_shell_reboot(self):
        runner = FakeRunner()
        runner.listing = "List of devices attached\nalpha sideload\n"
        with self.assertRaises(BridgeError):
            AdbClient(Path("adb"), runner).reboot("alpha", Target.SYSTEM)
        self.assertEqual(len(runner.calls), 1)

    def test_arbitrary_destination_rejected(self):
        runner = FakeRunner()
        with self.assertRaises(BridgeError):
            AdbClient(Path("adb"), runner).reboot("alpha", "download")
        self.assertEqual(runner.calls, [])

    def test_nonzero_reboot_does_not_return_receipt(self):
        runner = FakeRunner()
        runner.reboot_result = Result(1, stderr="device offline")
        with self.assertRaises(BridgeError) as raised:
            AdbClient(Path("adb"), runner).reboot("alpha", Target.RECOVERY)
        self.assertEqual(raised.exception.code, "error.offline")

    def test_missing_explicit_tool_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as folder, patch("shutil.which", return_value="/bin/true"):
            with self.assertRaises(BridgeError):
                resolve_adb(str(Path(folder) / "missing"), Path(folder))

    def test_missing_shell_evidence_does_not_imply_system_booted(self):
        observation = AdbClient(Path("adb"), lambda *_: Result(1)).observe(Device("a", "device"))
        self.assertEqual(observation.mode, "adb")
        self.assertFalse(observation.boot_completed)
        self.assertEqual(observation.boot_id, "")

    def test_subprocess_uses_literal_arguments(self):
        literal = "x & echo UNEXPECTED $(whoami) ;"
        result = run_process([sys.executable, "-c", "import sys; print(sys.argv[1])", literal], 5)
        self.assertEqual(result.stdout.strip(), literal)

    def test_timeout_is_not_command_success(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("adb", 1)):
            with self.assertRaises(BridgeError) as raised:
                run_process(["adb", "reboot"], 1)
        self.assertEqual(raised.exception.code, "error.timeout")

    def test_windows_adb_uses_no_console_or_powershell(self):
        completed = subprocess.CompletedProcess([], 0, "ok", "")
        with patch("subprocess.CREATE_NO_WINDOW", 0x08000000, create=True), patch(
                "chimpibridge.adb.sys.platform", "win32"), patch(
                "subprocess.run", return_value=completed) as execute:
            run_process(["adb.exe", "-s", "selected", "reboot", "recovery"], 12)
        self.assertEqual(execute.call_args.args[0], ["adb.exe", "-s", "selected", "reboot", "recovery"])
        self.assertFalse(execute.call_args.kwargs["shell"])
        self.assertEqual(execute.call_args.kwargs["creationflags"], 0x08000000)


class TransitionTests(unittest.TestCase):
    def pending(self, target=Target.RECOVERY, mode="adb"):
        before = Observation(Device("alpha", "device"), mode, BOOT_A, True)
        return Transition(RebootReceipt("alpha", target, before), started=0, timeout=90)

    def test_command_or_disconnect_alone_is_not_confirmation(self):
        pending = self.pending()
        self.assertEqual(pending.update([], None, 3), "waiting")
        self.assertEqual(pending.update([], None, 91), "unconfirmed")

    def test_other_phone_in_recovery_cannot_confirm_target(self):
        pending = self.pending()
        other = Device("beta", "recovery")
        self.assertEqual(pending.update([other], Observation(other, "recovery"), 3), "waiting")

    def test_android_reappearing_does_not_confirm_recovery(self):
        pending = self.pending()
        phone = Device("alpha", "device")
        self.assertEqual(pending.update([phone], Observation(phone, "adb", BOOT_B, True), 3), "waiting")

    def test_selected_recovery_is_confirmed(self):
        pending = self.pending()
        phone = Device("alpha", "recovery")
        self.assertEqual(pending.update([phone], Observation(phone, "recovery", BOOT_B), 3), "confirmed")

    def test_old_booted_state_does_not_confirm_a_new_restart(self):
        pending = self.pending(Target.SYSTEM)
        phone = Device("alpha", "device")
        self.assertEqual(pending.update([phone], Observation(phone, "adb", BOOT_A, True), 3), "waiting")

    def test_new_boot_id_confirms_restart_without_observed_disconnect(self):
        pending = self.pending(Target.SYSTEM)
        phone = Device("alpha", "device")
        self.assertEqual(pending.update([phone], Observation(phone, "adb", BOOT_B, True), 3), "confirmed")

    def test_restart_waits_for_boot_complete(self):
        pending = self.pending(Target.SYSTEM)
        phone = Device("alpha", "device")
        pending.update([], None, 2)
        self.assertEqual(pending.update([phone], Observation(phone, "adb", BOOT_B, False), 3), "waiting")
        self.assertEqual(pending.update([phone], Observation(phone, "adb", BOOT_B, True), 4), "confirmed")

    def test_restarting_recovery_requires_new_evidence(self):
        pending = self.pending(Target.RECOVERY, mode="recovery")
        phone = Device("alpha", "recovery")
        self.assertEqual(pending.update([phone], Observation(phone, "recovery", BOOT_A), 3), "waiting")


class ResourceTests(unittest.TestCase):
    def test_languages_have_identical_keys_and_format_fields(self):
        import string
        pt = json.loads((ROOT / "locales" / "pt-BR.json").read_text(encoding="utf-8"))
        en = json.loads((ROOT / "locales" / "en.json").read_text(encoding="utf-8"))
        self.assertEqual(pt.keys(), en.keys())
        for key in pt:
            fields = lambda text: {f for _, f, _, _ in string.Formatter().parse(text) if f}
            self.assertEqual(fields(pt[key]), fields(en[key]), key)

    def test_display_language_and_saved_override(self):
        self.assertEqual(choose_language("auto", ["pt_PT"]), "pt-BR")
        self.assertEqual(choose_language("en", ["pt-BR"]), "en")
        self.assertEqual(choose_language("auto", ["fr-FR", "pt-BR"]), "pt-BR")
        self.assertEqual(choose_language("auto", ["ja-JP"]), "en")

    def test_settings_and_history_persist_and_ignore_malformed_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder), ROOT)
            store.settings["language"] = "pt-BR"
            store.save_settings()
            store.add("log.started", version="0.1.0")
            again = Store(Path(folder), ROOT)
            self.assertEqual(again.settings["language"], "pt-BR")
            self.assertEqual(len(again.history), 1)
            (Path(folder) / "history.json").write_text('[null, {"key": 3}]', encoding="utf-8")
            self.assertEqual(Store(Path(folder), ROOT).history, [])

    def test_corrupt_settings_restore_defaults_without_touching_unrelated_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "settings.json").write_text("not json", encoding="utf-8")
            keep = root / "keep.txt"
            keep.write_text("keep", encoding="utf-8")
            store = Store(root, ROOT)
            self.assertEqual(store.settings["language"], "auto")
            self.assertEqual(keep.read_text(), "keep")

    def test_resources_are_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as folder, patch("os.getcwd", return_value=folder):
            self.assertEqual(app_root(), ROOT)
            self.assertEqual(I18n(app_root(), "pt-BR")("action.recovery"), "Entrar no Recovery")

    def test_uninstaller_manifest_does_not_recursively_erase_user_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / "stage"
            (stage / "lib").mkdir(parents=True)
            (stage / "lib" / "test.dll").write_bytes(b"example")
            output = root / "uninstall.nsh"
            uninstall_manifest(stage, output)
            text = output.read_text(encoding="utf-8")
            self.assertIn('Delete "$INSTDIR\\lib\\test.dll"', text)
            self.assertNotIn("RMDir /r", text)
            self.assertNotIn("AppData", text)


if __name__ == "__main__":
    unittest.main()
