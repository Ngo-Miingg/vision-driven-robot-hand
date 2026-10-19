param(
  [string]$ReleaseName = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$versionFile = Join-Path $projectRoot "VERSION"

if ([string]::IsNullOrWhiteSpace($ReleaseName)) {
  if (Test-Path $versionFile) {
    $ReleaseName = (Get-Content $versionFile -Raw).Trim()
  }
  if ([string]::IsNullOrWhiteSpace($ReleaseName)) {
    $ReleaseName = "robot_hand_realtime_handover"
  }
}

$releaseRoot = Join-Path $projectRoot "release"
$releaseDir = Join-Path $releaseRoot $ReleaseName
$zipPath = Join-Path $releaseRoot ($ReleaseName + ".zip")

New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null

if (Test-Path $releaseDir) {
  $resolvedRelease = (Resolve-Path $releaseDir).Path
  $resolvedRoot = (Resolve-Path $projectRoot).Path
  if (-not $resolvedRelease.StartsWith($resolvedRoot)) {
    throw "Refusing to clean unexpected path: $resolvedRelease"
  }
  Remove-Item -LiteralPath $releaseDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

$includeItems = @(
  ".gitattributes",
  ".gitignore",
  "README.md",
  "QUICKSTART.md",
  "HANDOVER.md",
  "HARDWARE_CHECKLIST.md",
  "KNOWN_ISSUES.md",
  "RELEASE_CHECKLIST.md",
  "VERSION",
  "requirements.txt",
  "setup_python_env.bat",
  "run_link_test.bat",
  "run_preview_cv.bat",
  "run_realtime_cv.bat",
  "run_master_control.bat",
  "docs",
  "firmware",
  "pc_client",
  "web_client",
  "tools",
  "scripts"
)

foreach ($item in $includeItems) {
  $from = Join-Path $projectRoot $item
  if (-not (Test-Path $from)) {
    continue
  }
  $to = Join-Path $releaseDir $item
  Copy-Item -LiteralPath $from -Destination $to -Recurse -Force
}

$removePatterns = @(
  ".venv",
  "release",
  "__pycache__",
  ".git"
)

foreach ($pattern in $removePatterns) {
  Get-ChildItem -Path $releaseDir -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq $pattern } |
    Remove-Item -Recurse -Force
}

Get-ChildItem -Path $releaseDir -Recurse -Force -Include "*.pyc","*.pyo","*.log","*.zip",".DS_Store","Thumbs.db" -ErrorAction SilentlyContinue |
  Remove-Item -Force

if (Test-Path $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path $releaseDir -DestinationPath $zipPath -CompressionLevel Optimal

$bad = Get-ChildItem -Path $releaseDir -Recurse -Force |
  Where-Object { $_.FullName -match "\\.venv|__pycache__|\\.pyc$|\\.pyo$|\\.zip$" }

if ($bad) {
  $bad | Select-Object FullName
  throw "Release contains excluded files."
}

Write-Host "Release directory: $releaseDir"
Write-Host "Release zip      : $zipPath"
Write-Host "Files            : $((Get-ChildItem -Path $releaseDir -Recurse -File).Count)"
