"""Qt Widgets interface. ADB runs on one bounded background worker at a time."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QObject, QRunnable, QSignalBlocker, QSize, Qt, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QPlainTextEdit,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from . import __version__
from .adb import AdbClient, BridgeError, Device, Target, Transition, resolve_adb
from .i18n import I18n
from .provision import cached_adb, install_platform_tools
from .storage import Store, app_root

PLATFORM_TOOLS_URL = "https://developer.android.com/tools/releases/platform-tools"
DRIVERS_URL = "https://developer.android.com/studio/run/oem-usb"


class TaskSignals(QObject):
    result = Signal(object)
    error = Signal(object)
    finished = Signal()


class Task(QRunnable):
    def __init__(self, job):
        super().__init__()
        self.job, self.signals = job, TaskSignals()

    @Slot()
    def run(self):
        try:
            self.signals.result.emit(self.job())
        except Exception as exc:
            self.signals.error.emit(exc)
        finally:
            self.signals.finished.emit()


class Window(QMainWindow):
    def __init__(self, store: Store | None = None, client_factory=AdbClient, *, auto_scan: bool = True,
                 tool_installer=install_platform_tools):
        super().__init__()
        self.root = app_root()
        self.store = store or Store()
        self.tr = I18n(self.root, self.store.settings["language"])
        self.client_factory = client_factory
        self.tool_installer = tool_installer
        self.auto_setup_attempted = False
        self.client = None
        self.devices: list[Device] = []
        self.transition: Transition | None = None
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.busy = False
        self.task = None
        self.success_handler = None
        self.operation = ""
        self.last_error = None
        self.last_notice = ("notice.ready", {}, False)
        self.bound_texts = []
        self._build()
        self._translate()
        self._resolve_client()
        self._record("log.started", version=__version__)
        self.timer = QTimer(self)
        self.timer.setInterval(2500)
        self.timer.timeout.connect(self.refresh)
        if auto_scan:
            self.timer.start()
            QTimer.singleShot(0, self.refresh)

    def label(self, key: str, *, muted=False, eyebrow=False) -> QLabel:
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        label.setProperty("muted", muted)
        label.setProperty("eyebrow", eyebrow)
        self.bound_texts.append((label, key))
        return label

    def button(self, key: str, handler) -> QPushButton:
        button = QPushButton()
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(36)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        button.clicked.connect(handler)
        self.bound_texts.append((button, key))
        return button

    @staticmethod
    def card() -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setProperty("card", True)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 17, 18, 17)
        layout.setSpacing(10)
        return frame, layout

    def _build(self):
        self.setWindowTitle(f"ChimpiBridge {__version__}")
        self.setWindowIcon(QIcon(str(self.root / "assets" / "mark.svg")))
        self.resize(1130, 830)
        self.setMinimumSize(950, 650)
        self.setStyleSheet((self.root / "assets" / "style.qss").read_text(encoding="utf-8"))
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 27, 18, 23)
        side.setSpacing(9)
        mark = QLabel()
        mark.setPixmap(self.windowIcon().pixmap(QSize(48, 48)))
        side.addWidget(mark)
        wordmark = QLabel("ChimpiBridge")
        wordmark.setObjectName("wordmark")
        side.addWidget(wordmark)
        version = QLabel(f"v{__version__}")
        version.setObjectName("version")
        side.addWidget(version)
        side.addSpacing(24)
        self.nav = []
        for index, key in enumerate(("nav.devices", "nav.guide", "nav.roadmap")):
            button = self.button(key, lambda checked=False, i=index: self._navigate(i))
            button.setCheckable(True)
            button.setProperty("nav", True)
            side.addWidget(button)
            self.nav.append(button)
        self.nav[0].setChecked(True)
        side.addStretch()
        side.addWidget(self.label("sidebar.footer", muted=True))
        layout.addWidget(sidebar)

        body = QWidget()
        content = QVBoxLayout(body)
        content.setContentsMargins(26, 26, 26, 22)
        content.setSpacing(16)
        heading = QHBoxLayout()
        headings = QVBoxLayout()
        headings.addWidget(self.label("app.stage", eyebrow=True))
        self.title = self.label("page.devices")
        self.title.setObjectName("pageTitle")
        headings.addWidget(self.title)
        self.subtitle = self.label("page.subtitle", muted=True)
        headings.addWidget(self.subtitle)
        heading.addLayout(headings, 1)
        lang_box = QVBoxLayout()
        lang_box.addWidget(self.label("settings.language", eyebrow=True))
        self.language = QComboBox()
        self.language.setMinimumWidth(132)
        self.language.addItem("", "auto")
        self.language.addItem("Português (BR)", "pt-BR")
        self.language.addItem("English", "en")
        index = self.language.findData(self.store.settings["language"])
        self.language.setCurrentIndex(max(0, index))
        self.language.currentIndexChanged.connect(self._change_language)
        lang_box.addWidget(self.language)
        heading.addLayout(lang_box)
        content.addLayout(heading)
        self.pages = QStackedWidget()
        self.pages.addWidget(self._devices_page())
        self.pages.addWidget(self._guide_page())
        self.pages.addWidget(self._roadmap_page())
        content.addWidget(self.pages, 1)
        layout.addWidget(body, 1)

    def _devices_page(self):
        page, layout = self._scroll_page()
        layout.setSpacing(14)
        adb_card, adb_layout = self.card()
        adb_layout.addWidget(self.label("adb.label", eyebrow=True))
        tools = QHBoxLayout()
        self.adb_path = QLineEdit()
        self.adb_path.setReadOnly(True)
        tools.addWidget(self.adb_path, 1)
        self.choose_button = self.button("adb.choose", self.choose_adb)
        tools.addWidget(self.choose_button)
        adb_layout.addLayout(tools)
        links = QHBoxLayout()
        self.setup_button = self.button("adb.setup", self.setup_adb)
        links.addWidget(self.setup_button)
        links.addWidget(self.button("adb.download", lambda: self.open_url(PLATFORM_TOOLS_URL)))
        self.test_button = self.button("adb.test", self.test_adb)
        links.addWidget(self.test_button)
        links.addStretch()
        adb_layout.addLayout(links)
        layout.addWidget(adb_card)

        middle = QHBoxLayout()
        middle.setSpacing(14)
        list_card, list_layout = self.card()
        list_card.setMinimumHeight(310)
        list_head = QHBoxLayout()
        list_head.addWidget(self.label("devices.title", eyebrow=True), 1)
        self.refresh_button = self.button("devices.refresh", self.refresh)
        list_head.addWidget(self.refresh_button)
        list_layout.addLayout(list_head)
        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(145)
        self.device_list.currentItemChanged.connect(self._selection_changed)
        list_layout.addWidget(self.device_list, 1)
        self.empty_hint = self.label("devices.empty", muted=True)
        list_layout.addWidget(self.empty_hint)
        self.count_label = self.label("devices.count", muted=True)
        list_layout.addWidget(self.count_label)
        middle.addWidget(list_card, 1)

        action_card, actions = self.card()
        action_card.setMinimumHeight(310)
        actions.setContentsMargins(16, 14, 16, 14)
        actions.setSpacing(6)
        self.selection_title = self.label("device.select")
        self.selection_title.setObjectName("selectionTitle")
        actions.addWidget(self.selection_title)
        self.serial_label = self.label("device.hint.none", muted=True)
        actions.addWidget(self.serial_label)
        self.state_label = QLabel()
        self.state_label.setObjectName("state")
        self.state_label.setTextFormat(Qt.TextFormat.PlainText)
        actions.addWidget(self.state_label)
        self.device_hint = self.label("device.hint.none", muted=True)
        actions.addWidget(self.device_hint)
        actions.addStretch()
        self.recovery_button = self.button("action.recovery", lambda: self.request_reboot(Target.RECOVERY))
        self.recovery_button.setObjectName("primary")
        self.recovery_button.setMinimumHeight(44)
        self.system_button = self.button("action.system", lambda: self.request_reboot(Target.SYSTEM))
        actions.addWidget(self.recovery_button)
        actions.addWidget(self.system_button)
        actions.addWidget(self.label("action.note", muted=True))
        middle.addWidget(action_card, 1)
        layout.addLayout(middle, 1)

        self.notice_frame = QFrame()
        self.notice_frame.setObjectName("notice")
        notice_layout = QVBoxLayout(self.notice_frame)
        notice_layout.setContentsMargins(14, 11, 14, 11)
        row = QHBoxLayout()
        self.notice_label = self.label("notice.ready")
        row.addWidget(self.notice_label, 1)
        self.stop_button = self.button("wait.stop", self.stop_waiting)
        self.stop_button.hide()
        row.addWidget(self.stop_button)
        notice_layout.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        notice_layout.addWidget(self.progress)
        layout.addWidget(self.notice_frame)

        log_card, log_layout = self.card()
        log_head = QHBoxLayout()
        log_head.addWidget(self.label("history.title", eyebrow=True), 1)
        log_head.addWidget(self.button("history.export", self.export_history))
        log_layout.addLayout(log_head)
        self.history_edit = QPlainTextEdit()
        self.history_edit.setReadOnly(True)
        self.history_edit.setFixedHeight(100)
        log_layout.addWidget(self.history_edit)
        layout.addWidget(log_card)
        return page

    def _scroll_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)
        scroll.setWidget(content)
        return scroll, layout

    def _guide_page(self):
        scroll, layout = self._scroll_page()
        for number in range(1, 5):
            frame, card_layout = self.card()
            card_layout.addWidget(self.label(f"guide.{number}.title"))
            card_layout.addWidget(self.label(f"guide.{number}.body", muted=True))
            if number == 1:
                card_layout.addWidget(self.button("adb.download", lambda: self.open_url(PLATFORM_TOOLS_URL)))
            elif number == 4:
                card_layout.addWidget(self.button("guide.drivers", lambda: self.open_url(DRIVERS_URL)))
            layout.addWidget(frame)
        layout.addWidget(self.label("guide.limit", muted=True))
        layout.addStretch()
        return scroll

    def _roadmap_page(self):
        scroll, layout = self._scroll_page()
        for number in range(1, 4):
            frame, card_layout = self.card()
            card_layout.addWidget(self.label(f"roadmap.{number}.title"))
            card_layout.addWidget(self.label(f"roadmap.{number}.body", muted=True))
            layout.addWidget(frame)
        layout.addWidget(self.label("roadmap.note", muted=True))
        layout.addStretch()
        return scroll

    def _navigate(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav):
            button.setChecked(i == index)
        self._translate()

    def _translate(self):
        # Dynamic labels are refreshed below after the static text pass.
        for widget, key in self.bound_texts:
            if key != "devices.count":
                widget.setText(self.tr(key))
        self.language.setItemText(0, self.tr("settings.auto"))
        self.adb_path.setPlaceholderText(self.tr("adb.auto"))
        self.history_edit.setPlaceholderText(self.tr("history.empty"))
        titles = ("page.devices", "page.guide", "page.roadmap")
        subtitles = ("page.subtitle", "guide.intro", "roadmap.intro")
        self.title.setText(self.tr(titles[self.pages.currentIndex()]))
        self.subtitle.setText(self.tr(subtitles[self.pages.currentIndex()]))
        self._render_devices()
        self._render_history()
        key, params, error = self.last_notice
        self.notice(key, error=error, **params)

    def _change_language(self):
        self.store.settings["language"] = self.language.currentData()
        self.tr = I18n(self.root, self.store.settings["language"])
        try:
            self.store.save_settings()
        except OSError:
            self.notice("error.storage", error=True)
        self._translate()

    def _resolve_client(self):
        try:
            path = resolve_adb(self.store.settings["adb_path"], self.root, cached_adb(self.store.root))
            self.client = self.client_factory(path)
            self.adb_path.setText(str(path))
            self.adb_path.setToolTip(str(path))
        except BridgeError as exc:
            self.client = None
            self.adb_path.setText(self.store.settings["adb_path"])
            if not (self.auto_setup_attempted and self.last_error and self.operation == "setup"):
                self.notice(exc.code, error=True)
        self._enabled()

    def setup_adb(self):
        if self.busy or self.transition or self.client is not None:
            return
        self.auto_setup_attempted = True
        self.notice("notice.adb_setup")
        self._record("log.adb_setup")
        self._work("setup", lambda: self.tool_installer(self.store.root), self._setup_done)

    def _setup_done(self, path):
        self.store.settings["adb_path"] = ""
        try:
            self.store.save_settings()
        except OSError:
            self.notice("error.storage", error=True)
        self.client = self.client_factory(path)
        self.adb_path.setText(str(path))
        self.adb_path.setToolTip(str(path))
        self._record("log.adb_ready")
        self.notice("notice.adb_ok")

    def choose_adb(self):
        selected, _ = QFileDialog.getOpenFileName(self, self.tr("settings.adb_title"),
            str(Path(self.store.settings["adb_path"]).parent) if self.store.settings["adb_path"] else "",
            self.tr("settings.adb_filter"))
        if not selected:
            return
        self.store.settings["adb_path"] = selected
        try:
            self.store.save_settings()
        except OSError:
            self.notice("error.storage", error=True)
        self.devices = []
        self._render_devices()
        self._resolve_client()
        self.test_adb()

    def _work(self, operation, job, success):
        if self.busy:
            return
        self.busy, self.operation, self.success_handler = True, operation, success
        self.task = Task(job)
        self.task.signals.result.connect(self._task_success)
        self.task.signals.error.connect(self._task_error)
        self.task.signals.finished.connect(self._task_finished)
        self._enabled()
        self.pool.start(self.task)

    @Slot(object)
    def _task_success(self, value):
        self.last_error = None
        self.success_handler(value)

    @Slot(object)
    def _task_error(self, exc):
        if not isinstance(exc, BridgeError):
            exc = BridgeError("error.unexpected", str(exc))
        signature = (exc.code, exc.detail)
        self.notice(exc.code, error=True)
        if signature != self.last_error:
            self._record("log.error", error_code=exc.code, detail=exc.detail)
        self.last_error = signature
        if self.operation == "scan":
            # A failed scan provides no evidence of disconnection or a mode change.
            self.devices = []
            self._render_devices()
            if self.transition and monotonic() - self.transition.started >= self.transition.timeout:
                self._finish_transition("unconfirmed")

    @Slot()
    def _task_finished(self):
        self.busy = False
        self.task = None
        self._enabled()
        if self.operation == "setup" and self.client is not None:
            QTimer.singleShot(0, self.refresh)

    def refresh(self):
        if self.busy:
            return
        if self.client is None:
            self._resolve_client()
        if self.client is None:
            if (sys.platform == "win32" and not self.store.settings["adb_path"]
                    and not self.auto_setup_attempted):
                self.setup_adb()
            return
        client = self.client
        pending_serial = self.transition.receipt.serial if self.transition else None

        def scan():
            devices = client.scan()
            current = next((device for device in devices if device.serial == pending_serial), None)
            return devices, client.observe(current) if current else None

        self._work("scan", scan, self._scan_done)

    def _scan_done(self, value):
        self.devices, observation = value
        self._render_devices()
        if self.transition:
            state = self.transition.update(self.devices, observation, monotonic())
            if state != "waiting":
                self._finish_transition(state)
            else:
                self.notice("notice.waiting", target=self.transition.receipt.target.value)
        elif self.last_notice[0] in {"notice.ready", "notice.empty", "notice.connected"} or self.last_notice[2]:
            self.notice("notice.connected" if self.devices else "notice.empty")

    def selected(self) -> Device | None:
        item = self.device_list.currentItem()
        if item:
            serial = item.data(Qt.ItemDataRole.UserRole)
            return next((d for d in self.devices if d.serial == serial), None)
        return None

    def _render_devices(self):
        selected = self.selected()
        serial = selected.serial if selected else None
        with QSignalBlocker(self.device_list):
            self.device_list.clear()
            for device in self.devices:
                text = f"{device.model or self.tr('device.no_model')}\n{self.tr('state.' + device.state)} · {device.serial}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, device.serial)
                self.device_list.addItem(item)
                if device.serial == serial:
                    self.device_list.setCurrentItem(item)
            if not serial and len(self.devices) == 1:
                self.device_list.setCurrentRow(0)
        self.empty_hint.setVisible(not self.devices)
        self.count_label.setText(self.tr("devices.count", count=len(self.devices)))
        self._selection_changed()

    def _selection_changed(self, *_):
        device = self.selected()
        self.selection_title.setText((device.model or self.tr("device.no_model")) if device else self.tr("device.select"))
        self.serial_label.setText(self.tr("device.serial", serial=device.serial) if device else "")
        self.state_label.setText(self.tr("state." + device.state) if device else "")
        hint = "none" if device is None else device.state
        if hint not in {"none", "device", "recovery", "unauthorized", "offline", "sideload"}:
            hint = "unavailable"
        self.device_hint.setText(self.tr("device.hint." + hint))
        self._enabled()

    def _enabled(self):
        if not hasattr(self, "recovery_button"):
            return
        device = self.selected()
        available = bool(self.client and device and device.ready and not self.busy and not self.transition)
        self.recovery_button.setEnabled(available)
        self.system_button.setEnabled(available)
        self.choose_button.setEnabled(not self.busy and not self.transition)
        self.setup_button.setEnabled(sys.platform == "win32" and self.client is None
                                     and not self.busy and not self.transition)
        self.test_button.setEnabled(bool(self.client) and not self.busy and not self.transition)
        self.refresh_button.setEnabled(not self.busy)
        self.device_list.setEnabled(not self.transition and not (self.busy and self.operation == "reboot"))
        self.stop_button.setVisible(bool(self.transition))
        self.progress.setVisible(bool(self.transition) or (self.busy and self.operation == "setup"))

    def request_reboot(self, target):
        device = self.selected()
        if self.busy or self.transition or not self.client or not device or not device.ready:
            return
        client, serial = self.client, device.serial
        self._record("log.request", target=target.value, serial=serial)
        self.notice("notice.sending")
        self._work("reboot", lambda: client.reboot(serial, target), self._reboot_done)

    def _reboot_done(self, receipt):
        self.transition = Transition(receipt, monotonic())
        self._record("log.sent", target=receipt.target.value, serial=receipt.serial)
        self.notice("notice.waiting", target=receipt.target.value)
        self._enabled()

    def _finish_transition(self, state):
        receipt = self.transition.receipt
        self.transition = None
        if state == "confirmed":
            self._record("log.confirmed", target=receipt.target.value, serial=receipt.serial)
            self.notice("notice.confirmed", target=receipt.target.value)
        else:
            self._record("log.unconfirmed", serial=receipt.serial)
            self.notice("notice.unconfirmed", error=True)
        self._enabled()

    def stop_waiting(self):
        if self.transition:
            self._record("log.cancelled", serial=self.transition.receipt.serial)
            self.transition = None
            self.notice("notice.cancelled")
            self._enabled()

    def test_adb(self):
        if self.client and not self.busy and not self.transition:
            self._work("version", self.client.version, self._version_done)

    def _version_done(self, version):
        self._record("log.adb", detail=version)
        self.notice("notice.adb_ok")

    def notice(self, key, *, error=False, **params):
        self.last_notice = (key, params, error)
        display_params = dict(params)
        if display_params.get("target") in {"system", "recovery"}:
            display_params["target"] = self.tr("target." + display_params["target"])
        self.notice_label.setText(self.tr(key, **display_params))
        self.notice_frame.setProperty("kind", "error" if error else "info")
        self.notice_frame.style().unpolish(self.notice_frame)
        self.notice_frame.style().polish(self.notice_frame)

    def _record(self, key, **params):
        try:
            self.store.add(key, **params)
        except OSError:
            self.notice("error.storage", error=True)
        self._render_history()

    def _history_text(self):
        lines = []
        for row in self.store.history:
            params = dict(row["params"])
            if "target" in params:
                params["target"] = self.tr("target." + params["target"])
            if "error_code" in params:
                params["message"] = self.tr(params.pop("error_code"))
            try:
                stamp = datetime.fromisoformat(row["time"]).strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"[{stamp}] {self.tr(row['key'], **params).rstrip()}")
            except (KeyError, TypeError, ValueError):
                continue
        return "\n\n".join(lines)

    def _render_history(self):
        self.history_edit.setPlainText(self._history_text())
        self.history_edit.verticalScrollBar().setValue(self.history_edit.verticalScrollBar().maximum())

    def export_history(self):
        path, _ = QFileDialog.getSaveFileName(self, self.tr("history.export"),
            self.tr("export.default"), self.tr("history.file"))
        if path:
            try:
                Path(path).write_text(self.tr("history.report") + "\n\n" + self._history_text() + "\n", encoding="utf-8")
                self.notice("notice.saved")
            except OSError:
                self.notice("error.export", error=True)

    @staticmethod
    def open_url(url):
        QDesktopServices.openUrl(QUrl(url))

    def closeEvent(self, event):
        if self.busy:
            self.notice("close.busy")
            event.ignore()
            return
        self.timer.stop()
        self.stop_waiting()
        event.accept()


def main() -> int:
    # A build-only startup probe verifies the frozen EXE without touching USB.
    import argparse
    import json
    import os
    import tempfile
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--smoke-test", type=Path)
    options, qt_args = parser.parse_known_args(sys.argv[1:])
    temporary = None
    if options.smoke_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        temporary = tempfile.TemporaryDirectory(prefix="chimpibridge-startup-")
    application = QApplication([sys.argv[0], *qt_args])
    application.setApplicationName("ChimpiBridge")
    application.setOrganizationName("SnoopyOS Company")
    application.setApplicationVersion(__version__)
    window = Window(Store(Path(temporary.name)) if temporary else None,
                    auto_scan=not bool(options.smoke_test))
    window.show()
    if options.smoke_test:
        def finish_probe():
            result = {"status": "error", "version": __version__}
            code = 1
            try:
                image = window.grab()
                icon = window.windowIcon().pixmap(QSize(48, 48))
                if image.isNull() or icon.isNull():
                    raise RuntimeError("Window or SVG icon could not be rendered")
                adb = resolve_adb("", app_root())
                result.update(status="ok", window_rendered=True, icon_rendered=True,
                              adb_bundled=adb.is_file(), language=window.tr.language)
                code = 0
            except Exception as exc:
                result["error"] = str(exc)
            try:
                options.smoke_test.parent.mkdir(parents=True, exist_ok=True)
                options.smoke_test.write_text(json.dumps(result, indent=2), encoding="utf-8")
            except OSError:
                code = 1
            window.close()
            application.exit(code)
        QTimer.singleShot(500, finish_probe)
    try:
        return application.exec()
    finally:
        if temporary:
            temporary.cleanup()
