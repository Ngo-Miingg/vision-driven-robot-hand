@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
  set "PYTHON_CMD=%CD%\%PYTHON_EXE%"
) else (
  set "PYTHON_CMD=python"
)

echo Robot Hand Realtime CV Test
echo Opening camera + skeleton realtime test with robot control.
echo Use Connect and ARM in the page before expecting robot motion.
echo.

cd web_client
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8080/realtime_cv_preview.html'"
"%PYTHON_CMD%" master_control_server.py --no-browser --esp-url ws://192.168.4.1:81
