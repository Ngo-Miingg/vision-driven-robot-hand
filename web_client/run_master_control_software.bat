@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=..\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo Robot Hand Master Control - Software Only
echo UI will open automatically.
echo Hardware bridge is simulated.
echo Voice, CV, dashboard, packet flow and logs stay active.
echo.

"%PYTHON_EXE%" master_control_server.py --esp-url ws://192.168.4.1:81 --simulate
