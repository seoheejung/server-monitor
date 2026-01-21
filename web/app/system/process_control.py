import psutil

def get_live_process(pid: int):
    """
    실시간 프로세스 재수집 (UI 신뢰 제거)

    서버에서 다시 확인
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

    # 시스템 프로세스 보호
    if is_system_process(proc, os_type):
        return {
            "result": "blocked",
            "message": "시스템 프로세스는 종료할 수 없습니다"
        }

    name = proc.name()
    # 1차: Soft Kill
    if soft_kill(proc):
        return {
            "result": "terminated",
            "method": "soft",
            "message": f"{name} 프로세스가 정상 종료되었습니다"
        }

    # 2차: Hard Kill
    hard_kill(proc)
    return {
        "result": "terminated",
        "method": "hard",
        "message": f"{name} 프로세스가 강제 종료되었습니다"
    }