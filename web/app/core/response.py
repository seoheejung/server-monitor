from datetime import datetime

def build_response(payload: dict) -> dict:
    """
    대시보드 응답 포맷
    """
    return {
        **payload,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def build_result(result: str, message: str, status: int) -> dict:
    """
    보안 예외 응답 포맷
    """
    return {
        "result": result,
        "message": message,
        "status": status,
    }