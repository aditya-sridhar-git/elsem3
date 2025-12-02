# Start Dashboard Script (Windows PowerShell)

Write-Host "Starting React Dashboard..." -ForegroundColor Cyan
Write-Host ""

# Navigate to dashboard directory
Set-Location dashboard

# Start the development server
Write-Host "Dashboard starting on http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev
