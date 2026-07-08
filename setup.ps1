<#
.SYNOPSIS
    AI-Facebook Poster setup script
.DESCRIPTION
    Create venv -> install deps -> init config
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==============================" -ForegroundColor Cyan
Write-Host " AI-Facebook Poster Setup" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# -- 1. Check Python --
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python not found. Install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $($python.Source)" -ForegroundColor Green

# -- 2. Create venv --
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment ..." -ForegroundColor Yellow
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] venv creation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] venv created: $venvPath" -ForegroundColor Green
} else {
    Write-Host "[OK] venv already exists" -ForegroundColor Green
}

# -- 3. Install deps --
$pip = Join-Path $venvPath "Scripts\pip.exe"
if (-not (Test-Path $pip)) {
    Write-Host "[ERROR] pip not found" -ForegroundColor Red
    exit 1
}

Write-Host "Installing dependencies (may take 1-2 min)..." -ForegroundColor Yellow
& $pip install -r (Join-Path $ProjectRoot "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# -- 4. Init .env --
$envTarget = Join-Path $ProjectRoot "work" ".env"
$envExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $envTarget)) {
    Copy-Item $envExample $envTarget
    Write-Host "[OK] .env created: $envTarget" -ForegroundColor Green
    Write-Host "[INFO] Edit work\.env and fill in your API keys" -ForegroundColor Yellow
} else {
    Write-Host "[OK] .env already exists" -ForegroundColor Green
}

# -- 5. Done --
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Activate:     . $activateScript" -ForegroundColor Yellow
Write-Host "  2. Edit config: notepad $envTarget" -ForegroundColor Yellow
Write-Host "  3. Test run:    python src\main.py" -ForegroundColor Yellow
Write-Host "  4. See docs:    README.md" -ForegroundColor Yellow
Write-Host ""
Pause
