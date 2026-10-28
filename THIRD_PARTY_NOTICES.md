# Third-party components

The source project uses Python, Qt for Python / PySide6 Essentials and shiboken6
The Windows builder uses PyInstaller and optionally NSIS
Their original notices are retained from installed distributions by the build script where available

- Python: https://www.python.org/psf/license/
- Qt for Python: https://doc.qt.io/qtforpython-6/licenses.html
- PyInstaller: https://pyinstaller.org/en/stable/license.html
- NSIS: https://nsis.sourceforge.io/License
- Android SDK Platform-Tools: https://developer.android.com/tools/releases/platform-tools

Android SDK binaries are not included in this source archive
The Windows build copies the complete official Platform-Tools directory supplied by the builder, including NOTICE.txt and source.properties

The bridge icon in assets/mark.svg was created specifically for this project

If ADB is missing at runtime on Windows, the application downloads the versioned official Google archive
https://dl.google.com/android/repository/platform-tools_r37.0.1-win.zip
SHA-256: 45f4d63113e895ebde0c90f194099a4676b6ac653bd28d54314a9e022bbc1a99
Its size and SHA-1 were checked against Google's repository2-3.xml on 2026-10-28 before recording this SHA-256
The complete package, including its notices, is retained in the user's data directory
