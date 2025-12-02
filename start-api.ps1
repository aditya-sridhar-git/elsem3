# Start API Server Script (Windows PowerShell)

Write-Host "Starting E-commerce Agent API Server..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the API server
Write-Host "API Server starting on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python api.py
