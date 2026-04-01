# 重启开发环境：先关闭所有后端进程，再重新启动完整调试

Write-Host "正在关闭后端进程 (port 8000)..." -ForegroundColor Cyan

$connections = netstat -ano 2>$null | Select-String ":\b8000\b"
if ($connections) {
    $pids = $connections |
        ForEach-Object { ($_ -split '\s+')[-1] } |
        Where-Object { $_ -match '^\d+$' -and $_ -ne '0' } |
        Select-Object -Unique

    foreach ($p in $pids) {
        try {
            Stop-Process -Id ([int]$p) -Force -ErrorAction Stop
            Write-Host "  已终止进程 PID: $p" -ForegroundColor Yellow
        } catch {
            Write-Host "  跳过 PID: $p ($($_.Exception.Message))" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "  未发现占用端口 8000 的进程" -ForegroundColor Green
}

# 等待端口释放
Start-Sleep -Seconds 1

Write-Host "正在启动开发服务器..." -ForegroundColor Cyan
npm run dev
