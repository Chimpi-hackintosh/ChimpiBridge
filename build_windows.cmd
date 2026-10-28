@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto ready
py -3.12 -m venv .venv
if errorlevel 1 goto python_missing
:ready
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" scripts\build_windows.py %*
if errorlevel 1 goto failed
echo Ready / Pronto - veja a pasta release
pause
exit /b 0
:python_missing
echo Install Python 3.12 x64 from https://www.python.org/downloads/windows/
echo Instale o Python 3.12 x64 e seu Python Launcher para gerar o aplicativo
pause
exit /b 1
:failed
echo Build failed / A compilacao falhou - veja a mensagem acima
pause
exit /b 1
