# CS2 Highlights Studio — Professional Launcher
$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Split-Path -Parent $scriptDir)
Set-Location $rootDir

# Setup console title and UTF-8 output
$Host.UI.RawUI.WindowTitle = "CS2 Highlights Studio — Launcher"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Clear-Host

Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor DarkCyan
Write-Host "║                    CS2 HIGHLIGHTS STUDIO v2.0                        ║" -ForegroundColor Cyan
Write-Host "║               AI Fragmovie & Tactical Video Engine                   ║" -ForegroundColor DarkCyan
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor DarkCyan
Write-Host ""

# 1. Check Python virtual environment
Write-Host "[1/4] " -NoNewline -ForegroundColor DarkGray
Write-Host "Проверка окружения Python и Node.js..." -ForegroundColor Yellow

$pythonExe = Join-Path $rootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "  [ОШИБКА] Виртуальное окружение (.venv) не найдено!" -ForegroundColor Red
    Write-Host "  Ожидаемый путь: $pythonExe" -ForegroundColor DarkGray
    Write-Host "  Создайте venv: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Gray
    Read-Host "`nНажмите Enter для выхода..."
    exit 1
}

$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) {
    Write-Host "  [ОШИБКА] Node.js или npm не найдены в переменной PATH!" -ForegroundColor Red
    Read-Host "`nНажмите Enter для выхода..."
    exit 1
}

Write-Host "  ✓ Python 3.12 (.venv) найден" -ForegroundColor Green
Write-Host "  ✓ Node.js ($($node.Version)) и npm найдены" -ForegroundColor Green

# 2. Check and clean conflicting ports
Write-Host "`n[2/4] " -NoNewline -ForegroundColor DarkGray
Write-Host "Проверка портов 8000 (Backend) и 5173 (Frontend)..." -ForegroundColor Yellow

$ports = @(8000, 5173)
$freedAny = $false
foreach ($p in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "  - Освобождение порта $p (PID $($proc.Id): $($proc.ProcessName))..." -ForegroundColor DarkYellow
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    $freedAny = $true
                }
            } catch {}
        }
    }
}
Start-Sleep -Milliseconds 600
Write-Host "  ✓ Порты 8000 и 5173 готовы к запуску" -ForegroundColor Green

# 3. Start Backend & Frontend
Write-Host "`n[3/4] " -NoNewline -ForegroundColor DarkGray
Write-Host "Запуск серверов в фоновом режиме..." -ForegroundColor Yellow

$backendLog = Join-Path $rootDir "backend.log"
$backendErr = Join-Path $rootDir "backend_err.log"
$backendProc = Start-Process -FilePath $pythonExe `
    -ArgumentList "-m", "uvicorn", "backend.api.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $rootDir `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError $backendErr `
    -WindowStyle Hidden `
    -PassThru

Write-Host "  ✓ Backend API запущен (PID: $($backendProc.Id))" -ForegroundColor Cyan

$frontendDir = Join-Path $rootDir "frontend"
$frontendLog = Join-Path $rootDir "frontend.log"
$frontendErr = Join-Path $rootDir "frontend_err.log"
$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev -- --host 127.0.0.1 --port 5173" `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput $frontendLog `
    -RedirectStandardError $frontendErr `
    -WindowStyle Hidden `
    -PassThru

Write-Host "  ✓ Frontend Studio запущен (PID: $($frontendProc.Id))" -ForegroundColor Cyan

# 4. Wait for Health Check
Write-Host "`n[4/4] " -NoNewline -ForegroundColor DarkGray
Write-Host "Ожидание готовности серверов (Health Check)..." -ForegroundColor Yellow

$backendReady = $false
$frontendReady = $false

for ($i = 0; $i -lt 35; $i++) {
    Start-Sleep -Milliseconds 500
    if (-not $backendReady) {
        try {
            $res = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 1
            if ($res.StatusCode -eq 200) { $backendReady = $true }
        } catch {}
    }
    if (-not $frontendReady) {
        try {
            $res = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 1
            if ($res.StatusCode -eq 200) { $frontendReady = $true }
        } catch {}
    }
    if ($backendReady -and $frontendReady) { break }
}

if (-not ($backendReady -and $frontendReady)) {
    Write-Host "`n  [ОШИБКА] Серверы не ответили вовремя!" -ForegroundColor Red
    if (Test-Path $backendErr) {
        Write-Host "--- Backend Error Log ---" -ForegroundColor Red
        Get-Content $backendErr -Tail 15
    }
    if (Test-Path $frontendErr) {
        Write-Host "--- Frontend Error Log ---" -ForegroundColor Red
        Get-Content $frontendErr -Tail 15
    }
    Read-Host "`nНажмите Enter для выхода..."
    exit 1
}

# Success Screen
Clear-Host
$Host.UI.RawUI.WindowTitle = "[ONLINE] CS2 Highlights Studio"

Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║             ● СТАТУС: СЕРВИСЫ АКТИВНЫ И РАБОТАЮТ (ONLINE)            ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  ● Студия (UI):       " -NoNewline -ForegroundColor Gray
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host "  ● Backend API:       " -NoNewline -ForegroundColor Gray
Write-Host "http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  ● Документация API:  " -NoNewline -ForegroundColor Gray
Write-Host "http://127.0.0.1:8000/docs" -ForegroundColor DarkCyan
Write-Host "  ● Здоровье API:      " -NoNewline -ForegroundColor Gray
Write-Host "http://127.0.0.1:8000/api/health" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  ● Логи процессов:    backend.log, frontend.log" -ForegroundColor DarkGray
Write-Host "──────────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Open Browser
Start-Process "http://localhost:5173"
Write-Host "✓ Веб-интерфейс открыт в браузере." -ForegroundColor Green
Write-Host ""

# Interactive Control Menu Loop
while ($true) {
    Write-Host "Управление:" -ForegroundColor Yellow
    Write-Host "  [1] Открыть студию в браузере повторно" -ForegroundColor White
    Write-Host "  [2] Проверить статус серверов (Ping)" -ForegroundColor White
    Write-Host "  [3] Выключить серверы и выйти (STOP)" -ForegroundColor Red
    Write-Host ""
    $choice = Read-Host "Выберите действие (1-3) или нажмите Enter для остановки"

    if ($choice -eq "1") {
        Start-Process "http://localhost:5173"
        Write-Host "✓ Браузер открыт.`n" -ForegroundColor Green
    }
    elseif ($choice -eq "2") {
        try {
            $b = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 2
            $f = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 2
            Write-Host "  ● Backend API:  " -NoNewline
            Write-Host "ONLINE (HTTP $($b.StatusCode))" -ForegroundColor Green
            Write-Host "  ● Frontend UI:  " -NoNewline
            Write-Host "ONLINE (HTTP $($f.StatusCode))`n" -ForegroundColor Green
        } catch {
            Write-Host "  [!] Ошибка проверки связи с серверами: $($_.Exception.Message)`n" -ForegroundColor Red
        }
    }
    else {
        # Shutdown
        Write-Host "`nОстановка серверов..." -ForegroundColor Yellow
        & (Join-Path $scriptDir "stop_app.ps1")
        break
    }
}
