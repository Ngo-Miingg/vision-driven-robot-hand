@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" (
  set "PYTHON_CMD=%CD%\%PYTHON_EXE%"
) else (
  set "PYTHON_CMD=python"
)

cd pc_client
"%PYTHON_CMD%" cv_sender_template.py
pause
