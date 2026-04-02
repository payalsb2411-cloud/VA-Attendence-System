$env:PYTHONPATH = "C:\attendence system\.build_lib;C:\attendence system\src"
Set-Location "C:\attendence system"
if (-not $env:ATTENDANCE_CERT_FILE -or -not $env:ATTENDANCE_KEY_FILE) {
    Write-Host "Set ATTENDANCE_CERT_FILE and ATTENDANCE_KEY_FILE first."
    Write-Host "Example:"
    Write-Host '$env:ATTENDANCE_CERT_FILE="C:\certs\fullchain.pem"'
    Write-Host '$env:ATTENDANCE_KEY_FILE="C:\certs\privkey.pem"'
    exit 1
}
.\.build311\Scripts\python.exe server\app.py
