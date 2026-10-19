@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=..\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo Robot Hand Master Control
echo UI will open automatically.
echo Browser control API   : /api/send
echo Fallback local WS     : ws://127.0.0.1:8765
echo ESP32 target WebSocket  : ws://192.168.4.1:81
echo Keep this window open while using the dashboard.
echo.

"%PYTHON_EXE%" master_control_server.py --esp-url ws://192.168.4.1:81
