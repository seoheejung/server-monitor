import os
import secrets
from datetime import datetime, timedelta, UTC

from fastapi import Cookie, HTTPException, Response, status

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

SESSION_COOKIE_NAME = "admin_session"
# 세션 유지 시간 (시간 단위)
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "4"))

# key: session_token (str), value: 만료 시각 (datetime)
# 서버 재시작 시 전부 사라짐
ACTIVE_SESSIONS: dict[str, datetime] = {}

def verify_admin_credentials(username: str | None, password: str | None) -> None:
    """
    관리자 아이디/비밀번호 검증

    - env에 설정된 값과 비교
    - 실패 시 401 반환
    """

    # 서버 설정 문제 (env 누락)
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin credentials are not configured",
        )

    # 입력값 누락
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing username or password",
        )

    # 값 비교 (timing attack 완화 위해 compare_digest 사용 권장)
    username_ok = secrets.compare_digest(username, ADMIN_USERNAME)
    password_ok = secrets.compare_digest(password, ADMIN_PASSWORD)

    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


def create_admin_session() -> str:
    """
    로그인 성공 시 호출

    - 랜덤 세션 토큰 생성
    - 만료 시각 설정
    - 서버 메모리에 저장
    """

    # 예측 불가능한 랜덤 토큰 생성
    token = secrets.token_urlsafe(32)

    # 만료 시각 계산 (현재 + 8시간)
    expires_at = datetime.now(UTC) + timedelta(hours=SESSION_EXPIRE_HOURS)

    # 세션 저장
    ACTIVE_SESSIONS[token] = expires_at

    return token


def cleanup_expired_sessions() -> None:
    """
    만료된 세션 제거

    - 별도 스케줄러 없이
    - 요청 처리 시마다 정리
    """

    now = datetime.now(UTC)

    # 만료된 토큰 목록 추출
    expired_tokens = [
        token
        for token, expires_at in ACTIVE_SESSIONS.items()
        if expires_at <= now
    ]

    # 삭제
    for token in expired_tokens:
        ACTIVE_SESSIONS.pop(token, None)


def issue_admin_cookie(response: Response, session_token: str) -> None:
    """
    로그인 성공 후 브라우저에 쿠키 설정

    - 쿠키 값은 비밀번호가 아니라 세션 토큰
    """

    response.set_cookie(
        key=SESSION_COOKIE_NAME,     # 쿠키 이름
        value=session_token,         # 랜덤 세션 토큰
        httponly=True,               # JS에서 접근 불가 (보안)
        samesite="strict",           # CSRF 완화
        secure=False,                # ⚠ HTTPS 운영 시 True로 변경
        path="/",                    # 전체 경로에서 사용
        max_age=SESSION_EXPIRE_HOURS * 60 * 60,  # 8시간 = 28800초
    )


def require_admin_cookie(admin_session: str | None = Cookie(default=None)) -> None:
    """
    보호된 API 접근 시 호출

    - 쿠키 존재 여부 확인
    - 서버가 발급한 세션인지 확인
    """

    # 만료 세션 정리
    cleanup_expired_sessions()

    # 쿠키 없음 → 인증 실패
    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin session",
        )

    # 서버에 없는 토큰 → 위조 또는 만료
    expires_at = ACTIVE_SESSIONS.get(admin_session)
    if not expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin session",
        )


def clear_admin_session(
    response: Response,
    admin_session: str | None = Cookie(default=None),
) -> None:
    """
    로그아웃 처리

    - 서버 세션 삭제
    - 브라우저 쿠키 제거
    """

    # 서버에서 세션 제거
    if admin_session:
        ACTIVE_SESSIONS.pop(admin_session, None)

    # 브라우저 쿠키 제거
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
    )