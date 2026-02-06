# Vision AI Microservices Startup Script
# This script starts all microservices in separate PowerShell windows

Write-Host "Starting Vision AI Microservices..." -ForegroundColor Green

# Function to start a service in a new window
function Start-Service {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Command
    )
    
    Write-Host "Starting $Name..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Path'; $Command"
    Start-Sleep -Seconds 1
}

# Start each service
Start-Service -Name "API Gateway" -Path "$PSScriptRoot\gateway" -Command "python gateway_app.py"
Start-Service -Name "Captioning Service" -Path "$PSScriptRoot\captionning\backend" -Command "python app.py"
Start-Service -Name "Masking Service" -Path "$PSScriptRoot\masking\backend" -Command "python app.py"
Start-Service -Name "Agent Chatbot" -Path "$PSScriptRoot\vision_agent\backend" -Command "python chatbot_app.py"
Start-Service -Name "OCR Service" -Path "$PSScriptRoot\ocr\backend" -Command "python main.py"
Start-Service -Name "React Frontend" -Path "$PSScriptRoot\frontend" -Command "npm run dev"

Write-Host ""
Write-Host "All services (including Frontend) started!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage URLs:" -ForegroundColor Yellow
Write-Host "  Frontend:   http://localhost:3000" -ForegroundColor White
Write-Host "  Gateway:    http://localhost:8000" -ForegroundColor White
Write-Host "  Captioning: http://localhost:8001" -ForegroundColor White
Write-Host "  Masking:    http://localhost:8002" -ForegroundColor White
Write-Host "  Chatbot:    http://localhost:8003" -ForegroundColor White
Write-Host "  OCR:        http://localhost:8004" -ForegroundColor White
Write-Host ""
Write-Host "Network Access:" -ForegroundColor Cyan
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*vEthernet*" }).IPAddress[0]
Write-Host "  Open on other devices: http://$($ip):3000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the services" -ForegroundColor Gray
