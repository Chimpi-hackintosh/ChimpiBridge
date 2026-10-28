"""Qt integration checks with an injected ADB adapter; no phone is accessed."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import time
import unittest
from pathlib import Path

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from chimpibridge.adb import BridgeError, Device, Observation, RebootReceipt, Target
from chimpibridge.storage import Store
from chimpibridge.ui import Window

ROOT = Path(__file__).resolve().parent.parent
APP = QApplication.instance() or QApplication([])


class StubClient:
    def __init__(self):
        self.devices = [Device("alpha", "device", "Galaxy J4 Core"), Device("beta", "unauthorized", "Android")]
        self.calls = []
        self.scan_error = None

    def scan(self):
        if self.scan_error:
            raise self.scan_error
        return self.devices[:]

    def observe(self, device):
        return Observation(device, "recovery" if device.state == "recovery" else "adb")

    def reboot(self, serial, target):
        self.calls.append((serial, target))
        return RebootReceipt(serial, target, Observation(next(d for d in self.devices if d.serial == serial), "adb"))

    def version(self):
        return "Android Debug Bridge version 1.0.41"


class InterfaceTests(unittest.TestCase):
    def wait_idle(self):
        QTest.qWait(5)
        deadline = time.monotonic() + 5
        while self.window.busy and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertFalse(self.window.busy)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        tool = root / "adb.exe"
        tool.write_bytes(b"stub - never executed")
        store = Store(root / "user", ROOT)
        store.settings.update({"language": "pt-BR", "adb_path": str(tool)})
        self.client = StubClient()
        self.window = Window(store, client_factory=lambda _: self.client)
        self.window.timer.stop()
        self.window.show()
        self.wait_idle()

    def tearDown(self):
        self.wait_idle()
        self.window.close()
        self.window.deleteLater()
        APP.processEvents()
        self.temp.cleanup()

    def test_multiple_devices_require_a_selection(self):
        self.assertIsNone(self.window.selected())
        self.assertFalse(self.window.recovery_button.isEnabled())
        self.assertEqual(self.client.calls, [])

    def test_recovery_waits_then_confirms_only_the_selected_device(self):
        self.window.device_list.setCurrentRow(0)
        self.assertTrue(self.window.recovery_button.isEnabled())
        self.window.recovery_button.click()
        self.wait_idle()
        self.assertEqual(self.client.calls, [("alpha", Target.RECOVERY)])
        self.assertIsNotNone(self.window.transition)
        self.assertFalse(any(row["key"] == "log.confirmed" for row in self.window.store.history))
        self.client.devices = [Device("alpha", "recovery", "Galaxy J4 Core")]
        self.window.refresh()
        self.wait_idle()
        self.assertIsNone(self.window.transition)
        self.assertEqual(self.window.last_notice[0], "notice.confirmed")
        self.assertTrue(any(row["key"] == "log.confirmed" for row in self.window.store.history))

    def test_other_phone_cannot_complete_monitoring(self):
        self.window.device_list.setCurrentRow(0)
        self.window.recovery_button.click()
        self.wait_idle()
        self.client.devices = [Device("beta", "recovery", "Other phone")]
        self.window.refresh()
        self.wait_idle()
        self.assertIsNotNone(self.window.transition)
        self.assertEqual(self.window.last_notice[0], "notice.waiting")

    def test_unauthorized_device_keeps_controls_disabled(self):
        self.window.device_list.setCurrentRow(1)
        self.assertFalse(self.window.recovery_button.isEnabled())
        self.assertIn("Desbloqueie", self.window.device_hint.text())

    def test_scan_failure_removes_stale_actionable_device(self):
        self.window.device_list.setCurrentRow(0)
        self.client.scan_error = BridgeError("error.offline", "device offline")
        self.window.refresh()
        self.wait_idle()
        self.assertIsNone(self.window.selected())
        self.assertFalse(self.window.system_button.isEnabled())
        self.assertEqual(self.window.last_notice[0], "error.offline")

    def test_language_switch_retranslates_waiting_status_and_logs(self):
        self.window.device_list.setCurrentRow(0)
        self.window.system_button.click()
        self.wait_idle()
        self.window.language.setCurrentIndex(self.window.language.findData("en"))
        self.assertEqual(self.window.system_button.text(), "Restart Android")
        self.assertIn("Android booted", self.window.notice_label.text())
        self.assertIn("Request accepted", self.window.history_edit.toPlainText())
        self.assertEqual(self.window.store.settings["language"], "en")

    def test_stop_monitoring_does_not_send_a_new_device_command(self):
        self.window.device_list.setCurrentRow(0)
        self.window.recovery_button.click()
        self.wait_idle()
        self.window.stop_waiting()
        self.assertIsNone(self.window.transition)
        self.assertEqual(len(self.client.calls), 1)


if __name__ == "__main__":
    unittest.main()
