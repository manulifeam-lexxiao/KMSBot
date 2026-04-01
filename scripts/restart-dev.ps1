# Restart dev: kill all backend processes, then start a fresh debug session

Write-Host "Stopping backend processes (port 8000)..." -ForegroundColor Cyan

$connections = netstat -ano 2>$null | Select-String ":\b8000\b"
if ($connections) {
    $pids = $connections |
        ForEach-Object { ($_ -split '\s+')[-1] } |
        Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } |
        Select-Object -Unique

    foreach ($p in $pids) {
        try {
            Stop-Process -Id ([int]$p) -Force -ErrorAction Stop
            Write-Host "  Killed PID: $p" -ForegroundColor Yellow
        } catch {
            Write-Host "  Skipped PID: $p ($($_.Exception.Message))" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "  No process found on port 8000" -ForegroundColor Green
}

# Wait for port release
Start-Sleep -Seconds 1

Write-Host "Starting dev server..." -ForegroundColor Cyan
npm run dev
