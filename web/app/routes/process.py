from fastapi import Depends, APIRouter
from pydantic import BaseModel

# 실제 프로세스 종료 로직 import
from app.services.system.process_control import terminate_process
from app.services.system.process_analyzer import get_process_list
from app.core.config import OS_TYPE
from app.core.security import require_admin_cookie

# 라우터 생성
router = APIRouter()

class TerminateRequest(BaseModel):
    """
    종료 요청 시 클라이언트가 보내는 데이터 구조

    FastAPI가 JSON을 자동으로 파싱
    pid가 숫자인지 자동 검증
    """
    pid: int

# 프론트/JS 확장 대비용
@router.get("/processes", dependencies=[Depends(require_admin_cookie)])
def process_api():
    return get_process_list(OS_TYPE)

@router.post("/process/terminate", dependencies=[Depends(require_admin_cookie)])
def terminate(req: TerminateRequest):
    """
    PID로 프로세스 종료
    """
    return terminate_process(req.pid, OS_TYPE)