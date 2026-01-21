#!/bin/bash
# =================================
# Server Monitor - Linux Prod Run
# =================================

echo "▶ Server Monitor (Linux Prod)"

PROJECT_DIR="/root/projects/server-monitor/web"

cd "$PROJECT_DIR" || {
  echo "❌ 프로젝트 디렉토리 이동 실패"
  exit 1
}

# 가상환경 활성화
if [ ! -f "venv/bin/activate" ]; then
  echo "❌ venv 가상환경이 없습니다."
  exit 1
fi

echo "▶ Activating virtualenv"
source venv/bin/activate

# FastAPI 서버 실행 (포그라운드)
echo "▶ Starting FastAPI (0.0.0.0:8000)"
uvicorn app.main:app --host 0.0.0.0 --port 8000
