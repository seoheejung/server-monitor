import psutil
from app.database.db import db_manager


def get_live_process(pid: int):
    """
    실시간 프로세스 재수집 (UI / 캐시 신뢰 제거 / 서버에서 다시 확인)
    """
    try:
        return psutil.Process(pid)
    except psutil.NoSuchProcess:
        return None # 해당 PID의 프로세스가 없음


def is_system_process(proc: psutil.Process, os_type: str):
    """
    시스템 프로세스인지 확인
    - Windows: SYSTEM 계정
    - Linux: root 계정
    """
    try:
        username = proc.username()
    except psutil.AccessDenied:
        # 정보 접근이 안되면 시스템 프로세스로 간주
        return True

    if os_type == "Windows":
        if username in ["SYSTEM", "LOCAL SERVICE", "NETWORK SERVICE"]:
            return True

    if os_type == "Linux":
        if username == "root":
            return True

    return False


def blocked_by_mongo_policy(proc: psutil.Process, os_type: str):
    """
    MongoDB 정책 기반 종료 차단 (보조 레이어)
    - 조회 우선순위:
      1) (name, platform = os_type)
      2) (name, platform = common)
    """
    if not db_manager.connected:
        return None

    name = proc.name().lower()

    # 1. OS 전용 정책 조회
    record = db_manager.get_process_policy(name, os_type)

    # 2. common 정책 fallback
    if not record:
        record = db_manager.get_process_policy(name, "common")
    
    if not record:
        return None  # Unknown Process → Mongo 정책 미적용

    policy = record.get("policy")
    if not policy:
        return None

    # 시스템 보호 정책
    if policy.get("is_system") is True:
        return {
            "result": "blocked",
            "reason": policy.get("reason", "System protected"),
            "message": "시스템 보호 정책에 의해 종료할 수 없는 프로세스입니다"
        }

    # 사용자 종료 차단 정책
    if policy.get("terminatable") is False:
        return {
            "result": "blocked",
            "reason": policy.get("reason", "Termination not allowed"),
            "message": "정책상 사용자 종료가 허용되지 않은 프로세스입니다"
        }

    return None


def soft_kill(proc: psutil.Process):
    """
    정상 종료 요청
    """
    try:
        proc.terminate() # SIGTERM or taskkill
        proc.wait(timeout=5) # 최대 5초 대기
        return True
    except psutil.TimeoutExpired:
        return False
    except psutil.AccessDenied:
        return False


def hard_kill(proc: psutil.Process):
    """
    강제 종료 (최후 수단)
    """
    try:
        proc.kill()   # SIGKILL / taskkill /F
        return True
    except psutil.AccessDenied:
        return False


def terminate_process(pid: int, os_type: str):
    """
    프로세스 종료 전체 흐름
    """ 
    proc = get_live_process(pid)
    if not proc:
        return {
            "result": "not_found",
            "message": "프로세스를 찾을 수 없습니다"
        }
    
    print(f"[TERMINATE] request pid={pid} name={proc.name()}")
    
    # 1. MongoDB 정책 차단 (연결된 경우만)
    mongo_block = blocked_by_mongo_policy(proc, os_type)
    if mongo_block:
        print(f"[TERMINATE] blocked by mongo policy: {mongo_block}")
        return mongo_block

    # 2. 시스템 프로세스 보호 (실시간 최종 보호)
    if is_system_process(proc, os_type):
        print(f"[TERMINATE] blocked by system process")
        return {
            "result": "blocked",
            "message": "SYSTEM 권한으로 실행 중인 프로세스는 <br> 안전상 자동 종료를 허용하지 않습니다"
        }

    name = proc.name()

    # 3. Soft Kill
    if soft_kill(proc):
        print(f"[TERMINATE] soft kill success")
        return {
            "result": "terminated",
            "method": "soft",
            "message": f"{name} <br> 프로세스가 정상 종료되었습니다"
        }

    # 4. Hard Kill
    if hard_kill(proc):
        print(f"[TERMINATE] hard kill success")
        return {
            "result": "terminated",
            "method": "hard",
            "message": f"{name} <br> 프로세스가 강제 종료되었습니다"
        }

    return {
        "result": "failed",
        "message": f"{name}<br>프로세스 종료에 실패했습니다"
    }