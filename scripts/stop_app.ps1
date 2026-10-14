# CS2 Highlights Studio — Professional Shutdown Script
$ErrorActionPreference = "SilentlyContinue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Split-Path -Parent $scriptDir)
Set-Location $rootDir

# Setup console title and UTF-8 output
$Host.UI.RawUI.WindowTitle = "[OFFLINE] CS2 Highlights Studio — Shutdown"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor DarkRed
Write-Host "║                 CS2 HIGHLIGHTS STUDIO — ОСТАНОВКА                    ║" -ForegroundColor Red
Write-Host "║              Завершение работы серверов и фоновых задач              ║" -ForegroundColor DarkRed
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor DarkRed
Write-Host ""

$stoppedList = @()
$ports = @(8000, 5173)

foreach ($p in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                $serviceName = if ($p -eq 8000) { "Backend API (FastAPI)" } else { "Frontend Studio (Vite)" }
                Write-Host "  [-] Остановка $serviceName (PID: $procId)... " -NoNewline -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "[ОСТАНОВЛЕНО]" -ForegroundColor Red
                $stoppedList += "$serviceName (PID $procId)"
            }
        }
    }
}

# Clean any remaining uvicorn processes if any
$uvicornProcs = Get-Process uvicorn -ErrorAction SilentlyContinue
if ($uvicornProcs) {
    foreach ($u in $uvicornProcs) {
        Write-Host "  [-] Завершение процесса uvicorn (PID: $($u.Id))... " -NoNewline -ForegroundColor Yellow
        Stop-Process -Id $u.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[ОСТАНОВЛЕНО]" -ForegroundColor Red
        $stoppedList += "Uvicorn (PID $($u.Id))"
    }
}

Start-Sleep -Milliseconds 600

# Final OFFLINE Status Banner
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Gray
Write-Host "║               ○ СТАТУС: ВСЕ СЕРВИСЫ ВЫКЛЮЧЕНЫ (OFFLINE)              ║" -ForegroundColor DarkGray
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Gray
Write-Host ""

if ($stoppedList.Count -gt 0) {
    Write-Host "  Остановленные службы:" -ForegroundColor White
    foreach ($item in $stoppedList) {
        Write-Host "    • $item" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  ✓ Порты 8000 и 5173 успешно освобождены." -ForegroundColor Green
} else {
    Write-Host "  ℹ️ Активных серверов на портах 8000 и 5173 не обнаружено (уже выключены)." -ForegroundColor Gray
}

Write-Host "──────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "Приложение безопасно остановлено.`n" -ForegroundColor White
Start-Sleep -Seconds 1
