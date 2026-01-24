import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import platform
import json
import os
import datetime

# 직접 생성한 시스템 정보 함수 import
from app.system.cpu import get_cpu_usage
from app.system.memory import get_memory_usage
from app.system.disk import get_disk_usage
from app.system.uptime import get_uptime
from app.system.service import get_service_status
from app.system.log import get_tail_log
from app.system.process_analyzer import get_process_list, sync_with_mongodb
from app.database.db import db_manager
from app.routes import process, admin
from app.core.config import OS_TYPE


# FastAPI app 생성
app = FastAPI()

# static 파일 등록 (CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API 라우터 등록
app.include_router(process.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# templates 등록
templates = Jinja2Templates(directory="app/templates")

# DB에 넣을 mork Data
JSON_FILE_PATH = "app/data/known_processes.json"

def usage_class(value):
    if value < 60:
        return "good"
    elif value < 80:
        return "warn"
    return "bad"

# 주소 http://127.0.0.1:8000/
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # 브라우저로 접속했을 때 보여줄 메인 화면
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage(OS_TYPE)
    uptime = get_uptime()

    # 2. 서비스 상태 수집 (딕셔너리 형태로 자동화)
    services_to_check = ["nginx", "sshd", "rsyslog", "python", "docker"]
    service_results = {
        name: get_service_status(name, OS_TYPE)
        for name in services_to_check
    }

    LOG_FILE = "/var/log/messages"
    logs = get_tail_log(LOG_FILE, 10, OS_TYPE)

    processes = get_process_list(OS_TYPE)


    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,

            # 시스템 자원
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "uptime": uptime,
            "cpu_class": usage_class(cpu),
            "memory_class": usage_class(memory),

            # 서비스 상태 (전체 딕셔너리 전달)
            "services": service_results,

            # 로그
            "logs": logs,
            "log_source": LOG_FILE,
            
            # 프로세스 분석 결과
            "processes": processes, 

            "os_type": OS_TYPE
        }
    )

# DevTools(개발자 도구)나 특정 크롬 확장 프로그램이 서버의 상세 정보를 파악하기 위해 자동으로 던지는 요청 막기
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def ignore_chrome_devtools():
    # 204 No Content를 반환하여 에러 로그가 남지 않게 합니다.
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# 서버 시작 시 실행
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


        # 3. DB에 시딩
        db_data = []
        if db_manager.db is not None:
            db_manager.seed_initial_data(local_data)
            # DB에서 정제된 최종 데이터 가져오기
            db_data = db_manager.get_known_processes()
        else: 
            # DB 연결 실패 시 JSON 파일 데이터 그대로 사용 (Fallback)
            db_data = local_data
            print("⚠️ DB 연결 실패. JSON 로컬 데이터를 엔진에 로드 진행")
        
        # 4. 메모리 캐시 동기화
        sync_with_mongodb(db_data, OS_TYPE)
        print(f"🚀 분석 엔진 준비 완료 (OS: {OS_TYPE}, 로드된 프로세스: {len(db_data)}개)")
        
    except Exception as e:
        print(f"❌ Startup 초기화 오류: {e}")

# 서버 종료 시 실행
@app.on_event("shutdown")
def shutdown_event():
    db_manager.close()
