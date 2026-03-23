from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from app.core.security import (
    verify_admin_credentials,
    create_admin_session,
    issue_admin_cookie,
    clear_admin_session,
)

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
def login_for_dashboard(payload: LoginRequest, response: Response):
    """
    관리자 로그인
    """
    verify_admin_credentials(payload.username, payload.password)

    session_token = create_admin_session()
    issue_admin_cookie(response, session_token)

    return {"result": "ok"}


@router.post("/auth/logout")
def logout_for_dashboard(
    response: Response,
    admin_session: str | None = Cookie(default=None),
):
    """
    관리자 로그아웃
    """
    clear_admin_session(response, admin_session)
    return {"result": "ok"}