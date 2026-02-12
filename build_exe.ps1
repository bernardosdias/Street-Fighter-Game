param(
    [string]$Name = "StreetFighterGame"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Virtual environment not found at .\.venv. Create it first."
}

Write-Host "Building $Name executable folder..."

.\.venv\Scripts\python.exe -m PyInstaller `
    --noconfirm `
    --clean `
    --name $Name `
    --onedir `
    --add-data "multimedia;multimedia" `
    main.py

Write-Host "Build complete: dist\$Name\$Name.exe"

