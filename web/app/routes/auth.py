from fastapi import APIRouter, Header, Response

from app.core.security import verify_admin_api_key, issue_admin_cookie

router = APIRouter()


@router.post("/auth")
def login_for_dashboard(
    response: Response,
    x_api_key: str | None = Header(default=None),
):
    """
    관리자 API 키를 검증하고 대시보드 접근용 세션 쿠키를 발급
    """
    verify_admin_api_key(x_api_key)
    issue_admin_cookie(response)
    return {"result": "ok"}