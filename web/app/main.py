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

from app.services.system.process_analyzer import sync_with_mongodb
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
    서버가 시작될 때 MongoDB에서 데이터를 가져와 메모리 캐시를 초기화
    """
    try:
        # 1. DB 연결
        db_manager.connect()
        
        # 2. JSON 파일에서 데이터 로드
        local_data = load_and_validate_process_data(JSON_FILE_PATH)

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
