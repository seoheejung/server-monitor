from fastapi import Depends, APIRouter
from app.core.response import build_result
from app.repositories.db import db_manager
from app.services.system.process_analyzer import sync_with_mongodb
from app.core.config import OS_TYPE
from app.core.security import require_admin_cookie

router = APIRouter()


@router.post("/admin/sync-now", dependencies=[Depends(require_admin_cookie)])
def manual_sync():
    """
    관리자가 호출 시 MongoDB에서 최신 known_processes를 다시 로드하여 메모리 캐시를 즉시 갱신
    """
    try:
        # DB 연결 상태 확인
        if db_manager.db is None:
            db_manager.connect()
        
        # DB 최신 데이터 조회
        db_data = db_manager.get_known_processes()

        if not db_data:
            return build_result(
                "warning",
                "DB에 데이터가 없습니다. 동기화가 건너뛰어졌습니다.",
                204
            )
        
        # 메모리 캐시 갱신
        sync_with_mongodb(db_data, OS_TYPE)

        return build_result(
            "success",
            f"성공적으로 {len(db_data)}개의 프로세스 데이터를 동기화했습니다.",
            200
        )

    except Exception as e:
        return build_result(
            "error",
            f"동기화 중 오류 발생: {str(e)}",
            500
        )