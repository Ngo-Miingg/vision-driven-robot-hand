$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ModelsDir = Join-Path $ProjectRoot "models"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

$VoskModels = @(
  @{
    Name = "vosk-model-small-vn-0.4"
    Url = "https://alphacephei.com/vosk/models/vosk-model-small-vn-0.4.zip"
  },
  @{
    Name = "vosk-model-small-en-us-0.15"
    Url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
  }
)

function Ensure-Directory([string]$PathValue) {
  if (-not (Test-Path -LiteralPath $PathValue)) {
    New-Item -ItemType Directory -Path $PathValue | Out-Null
  }
}

function Ensure-VoskModel([hashtable]$ModelInfo) {
  $TargetDir = Join-Path $ModelsDir $ModelInfo.Name
  if (Test-Path -LiteralPath $TargetDir) {
    Write-Host "[voice] Model already present: $($ModelInfo.Name)"
    return
  }

  $ZipPath = Join-Path $env:TEMP "$($ModelInfo.Name).zip"
  $ExtractRoot = Join-Path $env:TEMP "$($ModelInfo.Name)-extract"

  Write-Host "[voice] Downloading $($ModelInfo.Name)..."
  Invoke-WebRequest -Uri $ModelInfo.Url -OutFile $ZipPath

  if (Test-Path -LiteralPath $ExtractRoot) {
    Remove-Item -LiteralPath $ExtractRoot -Recurse -Force
  }
  New-Item -ItemType Directory -Path $ExtractRoot | Out-Null

  Write-Host "[voice] Extracting $($ModelInfo.Name)..."
  Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractRoot -Force

  $ExtractedDir = Join-Path $ExtractRoot $ModelInfo.Name
  if (-not (Test-Path -LiteralPath $ExtractedDir)) {
    throw "Extracted model folder not found: $ExtractedDir"
  }

  Move-Item -LiteralPath $ExtractedDir -Destination $TargetDir
  Remove-Item -LiteralPath $ZipPath -Force
  Remove-Item -LiteralPath $ExtractRoot -Recurse -Force
  Write-Host "[voice] Installed model: $($ModelInfo.Name)"
}

Ensure-Directory $ModelsDir

if (Test-Path -LiteralPath $PythonExe) {
  Write-Host "[voice] Ensuring Python packages..."
  & $PythonExe -m pip install --disable-pip-version-check sounddevice vosk
} else {
  Write-Host "[voice] Python venv not found at $PythonExe"
}

foreach ($Model in $VoskModels) {
  Ensure-VoskModel $Model
}

Write-Host "[voice] Pulling Ollama model qwen2.5:3b..."
ollama pull qwen2.5:3b

Write-Host ""
Write-Host "[voice] Offline voice bootstrap complete."
Write-Host "[voice] Vosk models:"
Get-ChildItem -LiteralPath $ModelsDir | ForEach-Object { Write-Host "  - $($_.Name)" }
Write-Host "[voice] Ollama models:"
ollama list
