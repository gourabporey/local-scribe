#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Move to script directory
Set-Location -Path $PSScriptRoot

Write-Host "[1/4] Creating Python virtual environment (if missing)"
if (-not (Test-Path -Path 'venv')) {
    python -m venv venv
}

Write-Host "[2/4] Activating venv and upgrading pip"
& "$PSScriptRoot/venv/Scripts/Activate.ps1"
python -m pip install --upgrade pip

Write-Host "[3/4] Installing Python dependencies"
pip install `
  sounddevice `
  vosk `
  PySide6 `
  playsound `
  pynput

$ModelDir = 'vosk-model-small-en-in-0.4'
$ModelZip = "$ModelDir.zip"
$ModelUrl = "https://alphacephei.com/vosk/models/$ModelZip"

Write-Host "[4/4] Ensuring Vosk model '$ModelDir' is present"
if (-not (Test-Path -Path $ModelDir)) {
  Write-Host "Downloading $ModelZip ..."
  Invoke-WebRequest -Uri $ModelUrl -OutFile $ModelZip
  Write-Host "Unzipping $ModelZip ..."
  Expand-Archive -LiteralPath $ModelZip -DestinationPath . -Force
  Remove-Item -LiteralPath $ModelZip -Force
} else {
  Write-Host "Model directory '$ModelDir' already exists; skipping download."
}

Write-Host "Setup complete. To run the app:" -ForegroundColor Green
Write-Host "  .\\venv\\Scripts\\activate; python main.py"


