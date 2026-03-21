from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)

from app.services.system.process_analyzer import (
    sync_with_mongodb,
    CACHED_KNOWN_PROCS,
)
from app.repositories.db import db_manager
from app.routes import process, admin, auth, dashboard 
from app.core.config import OS_TYPE
from app.core.security import issue_admin_cookie
from app.services.init.process_seed import load_and_validate_process_data

logger = logging.getLogger(__name__)

# FastAPI app 생성
app = FastAPI()

# static 파일 등록 (CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API 라우터 등록
app.include_router(process.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# templates 등록
templates = Jinja2Templates(directory="app/templates")

# DB에 넣을 mork Data
JSON_FILE_PATH = "data/known_processes.json"

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
    서버 시작 시 known_processes 데이터를 메모리 캐시에 로드

    정책:   
    - JSON 파일은 필수 초기 데이터
    - MongoDB 사용 가능 시 DB 기준으로 캐시 구성
    - MongoDB 사용 불가 시 로컬 JSON fallback으로 기동
    """
    try:
        # 앱 기동의 기준이 되는 기본 데이터
        local_data = load_and_validate_process_data(JSON_FILE_PATH)
        try:
            db_manager.connect()
            if db_manager.db is None:
                raise RuntimeError("MongoDB 연결 실패")
            
            # JSON 원본 데이터를 DB에 시딩
            db_manager.seed_initial_data(local_data)

            # DB에서 정제된 최종 데이터를 다시 읽어 캐시 구성
            db_data = db_manager.get_known_processes()
            
            # 메모리 캐시 동기화
            sync_with_mongodb(db_data, OS_TYPE)
            logger.info(
                "🚀 분석 엔진 준비 완료 (OS: %s, 로드된 프로세스: %s개)",
                OS_TYPE,
                len(CACHED_KNOWN_PROCS),
            )
        except Exception:
            logger.exception("⚠️ MongoDB 사용 불가 - 로컬 JSON fallback으로 기동")

            # DB 실패 시 로컬 JSON 기준으로 캐시 구성
            sync_with_mongodb(local_data, OS_TYPE)

            logger.info(
                "🚀 분석 엔진 준비 완료 (OS: %s, source: local_json, 캐시 엔트리 수: %s개)",
                OS_TYPE,
                len(CACHED_KNOWN_PROCS),
            )
    except Exception:
        logger.exception("❌ startup 실패 - 필수 초기 데이터 로드 불가")
        raise

@app.on_event("shutdown")
def shutdown_event():
    """
    서버가 종료될 때 DB 연결을 끊음
    """
    db_manager.close()
