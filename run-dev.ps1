# ================================
# Server Monitor - Windows Dev Run
# ================================

Write-Host "▶ Server Monitor (Windows Dev)"

# 프로젝트 루트 이동
Set-Location "$PSScriptRoot\web"

# 가상환경 활성화
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Error "❌ venv 가상환경이 없습니다. 먼저 생성하세요."
    exit 1
}

Write-Host "▶ Activating virtualenv"
.\venv\Scripts\Activate.ps1

# FastAPI 서버 실행
Write-Host "▶ Starting FastAPI (reload mode)"
uvicorn app.main:app --reload
