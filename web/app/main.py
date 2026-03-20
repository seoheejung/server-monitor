from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)

# 직접 생성한 시스템 정보 함수 import
from app.system.cpu import get_cpu_usage
from app.system.memory import get_memory_usage
from app.system.disk import get_disk_usage
from app.system.uptime import get_uptime
from app.system.service import get_service_status
from app.system.log import get_tail_log
from app.system.process_analyzer import get_process_list, sync_with_mongodb
from app.database.db import db_manager
from app.routes import process, admin, auth
from app.core.config import OS_TYPE
from app.core.security import require_admin_cookie, issue_admin_cookie

logger = logging.getLogger(__name__)

# FastAPI app 생성
app = FastAPI()

# static 파일 등록 (CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API 라우터 등록
app.include_router(process.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# templates 등록
templates = Jinja2Templates(directory="app/templates")

# DB에 넣을 mork Data
JSON_FILE_PATH = "data/known_processes.json"

def usage_class(value):
    if value < 60:
        return "good"
    elif value < 80:
        return "warn"
    return "bad"

def collect_dashboard_data() -> dict:
    """
    기본 모니터링 데이터 수집 함수
    """
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage(OS_TYPE)
    uptime = get_uptime()

    services_to_check = ["nginx", "sshd", "rsyslog", "python", "docker"]
    service_results = {
        name: get_service_status(name, OS_TYPE)
        for name in services_to_check
    }

    log_file = "/var/log/messages"
    logs = get_tail_log(log_file, 10, OS_TYPE)
    processes = get_process_list(OS_TYPE)

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "uptime": uptime,
        "cpu_class": usage_class(cpu),
        "memory_class": usage_class(memory),
        "os_type": OS_TYPE,
        "services": service_results,
        "logs": logs,
        "log_source": log_file,
        "processes": processes,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """
    브라우저 메인 화면 렌더링 + 관리자 세션 자동 발급
    """
    response = templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
        }
    )
    issue_admin_cookie(response)
    return response

@app.get("/api/dashboard", dependencies=[Depends(require_admin_cookie)])
def dashboard_api():
    """
    대시보드 부분 갱신용 JSON API
    - 프론트 JS가 60초마다 호출
    """
    return collect_dashboard_data()

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def ignore_chrome_devtools():
    """
    DevTools(개발자 도구)나 특정 크롬 확장 프로그램이 
    서버의 상세 정보를 파악하기 위해 자동으로 던지는 요청 막기용
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.on_event("startup")
def startup_event():
    """
    서버가 시작될 때 MongoDB에서 데이터를 가져와 메모리 캐시를 초기화
    """
    try:
        # 1. DB 연결
        db_manager.connect()

        # 2. JSON 파일에서 데이터 로드
        local_data = []
        if os.path.exists(JSON_FILE_PATH):
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                local_data = json.load(f)

            for i, item in enumerate(local_data):
                name = item.get("name")
                if not isinstance(name, str) or not name.strip():
                    logger.error("잘못된 항목 발견 (index=%s): %s", i, item)
                    break
            else:
                logger.info("name 필드 이상 없음")


        # 3. DB에 시딩
        db_data = []
        if db_manager.db is not None:
            db_manager.seed_initial_data(local_data)
            # DB에서 정제된 최종 데이터 가져오기
            db_data = db_manager.get_known_processes()
        else: 
            # DB 연결 실패 시 JSON 파일 데이터 그대로 사용 (Fallback)
            db_data = local_data
            logger.warning("⚠️ DB 연결 실패. JSON 로컬 데이터를 엔진에 로드 진행")
        
        # 4. 메모리 캐시 동기화
        sync_with_mongodb(db_data, OS_TYPE)
        logger.info(
            "🚀 분석 엔진 준비 완료 (OS: %s, 로드된 프로세스: %s개)",
            OS_TYPE,
            len(db_data),
        )
        
    except Exception:
        logger.exception("startup_event 실행 중 예외 발생")
        raise

@app.on_event("shutdown")
def shutdown_event():
    """
    서버가 종료될 때 DB 연결을 끊음
    """
    db_manager.close()
