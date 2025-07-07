Write-Host "Starting Anton AI Assistant..." -ForegroundColor Green
Set-Location -Path $PSScriptRoot
.\venv\Scripts\Activate.ps1
python app.py