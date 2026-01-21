from fastapi import APIRouter
import datetime

from app.database.db import db_manager
from app.system.process_analyzer import sync_with_mongodb
from app.core.config import OS_TYPE

router = APIRouter()


@router.get("/api/admin/sync-now")
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
            return {
                "status": "warning",
                "message": "DB에 데이터가 없습니다. 동기화가 건너뛰어졌습니다."
            }
        
        # 메모리 캐시 갱신
        sync_with_mongodb(db_data, OS_TYPE)

        return {
            "status": "success",
            "message": f"성공적으로 {len(db_data)}개의 프로세스 데이터를 동기화했습니다.",
            "os_type": OS_TYPE,
            "timestamp": datetime.datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"동기화 중 오류 발생: {str(e)}"
        }