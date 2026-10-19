@echo off
setlocal
cd /d "%~dp0"
if not exist "web_client\master_control_server.py" (
  echo ERROR: Copy this Docker kit to the root robot_hand_realtime folder.
  echo Expected: web_client\master_control_server.py
  pause
  exit /b 1
)
where docker >nul 2>&1
if errorlevel 1 (
  echo ERROR: Install Docker Desktop for Windows and start it first.
  pause
  exit /b 1
)
if not exist ".env" copy ".env.example" ".env" >nul

echo Building and starting Robot Hand dashboard...
docker compose up -d --build
if errorlevel 1 (
  echo ERROR: Docker Compose failed. Run docker compose logs --tail=100
  pause
  exit /b 1
)

docker compose ps
start "" "http://127.0.0.1:8080/master_control.html"
echo Dashboard: http://127.0.0.1:8080/master_control.html
echo ESP32 must be reachable from Windows/Docker at 192.168.4.1:81.
pause
