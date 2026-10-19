$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
  throw "Missing .venv. Run .\setup_python_env.bat first."
}

$cvScript = Join-Path $projectRoot "pc_client\cv_sender_template.py"
$serverScript = Join-Path $projectRoot "web_client\master_control_server.py"
$htmlFile = Join-Path $projectRoot "web_client\master_control.html"

Write-Host "Running Python self-test..."
& $pythonExe $cvScript --self-test

Write-Host "Checking Python syntax..."
& $pythonExe -m py_compile $serverScript

Write-Host "Checking dashboard JavaScript syntax..."
node -e "const fs=require('fs'); const html=fs.readFileSync(process.argv[1],'utf8'); const m=html.match(/<script>([\s\S]*?)<\/script>/); if(!m) throw new Error('No script block'); new Function(m[1]); console.log('master_control.js syntax ok');" $htmlFile

Get-ChildItem -Path $projectRoot -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.PSIsContainer -and $_.Name -eq "__pycache__" -and $_.FullName -notmatch "\\release\\" } |
  Remove-Item -Recurse -Force

Write-Host "Verification finished."
