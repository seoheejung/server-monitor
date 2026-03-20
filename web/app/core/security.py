import os
import secrets

from fastapi import Cookie, Header, HTTPException, Response, status

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
SESSION_COOKIE_NAME = "admin_session"


def verify_admin_api_key(raw_key: str | None) -> None:
    """
    전달받은 관리자 API 키가 환경변수 값과 일치하는지 검증 (최초 로그인용)
    """
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_API_KEY is not configured",
        )

    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if not secrets.compare_digest(raw_key, ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def issue_admin_cookie(response: Response) -> None:
    """
    인증이 완료된 관리자 세션 쿠키를 응답에 발급 (세션 발급용)
    """
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=ADMIN_API_KEY,
        httponly=True,
        samesite="strict",
        secure=False,   # HTTPS 아니면 False, HTTPS면 True
        path="/",
    )


def require_admin_cookie(admin_session: str | None = Cookie(default=None)) -> None:
    """
    요청에 포함된 관리자 세션 쿠키가 유효한지 검증 (이후 API 보호용)
    """
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_API_KEY is not configured",
        )

    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin session",
        )

    if not secrets.compare_digest(admin_session, ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin session",
        )