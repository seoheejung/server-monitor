from datetime import datetime

from fastapi import APIRouter, Query, Depends
from typing import Optional

from app.core.config import OS_TYPE
from app.services.system.cpu import get_cpu_usage
from app.services.system.memory import get_memory_usage
from app.services.system.disk import get_disk_usage
from app.services.system.uptime import get_uptime
from app.services.system.service import get_service_status
from app.services.system.log import get_tail_log
from app.services.system.process_analyzer import get_process_list
from app.core.security import require_admin_cookie

router = APIRouter(prefix="/dashboard", tags=["dashboard"],
    dependencies=[Depends(require_admin_cookie)])

def usage_class(value):
    if value < 60:
        return "good"
    elif value < 80:
        return "warn"
    return "bad"

@router.get("/summary")
def dashboard_summary():
    """
    시스템 요약 정보
    - CPU
    - 메모리
    - 디스크
    - 호스트 정보
    - 마지막 갱신 시각
    """
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage(OS_TYPE)
    uptime = get_uptime()

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "uptime": uptime,
        "cpu_class": usage_class(cpu),
        "memory_class": usage_class(memory),
        "os_type": OS_TYPE,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/processes")
def dashboard_processes():
    """
    프로세스 목록
    - PID
    - 이름
    - CPU%
    - Memory%
    - 상태
    - 포트 목록
    """
    processes = get_process_list(OS_TYPE)

    return {
        "processes": processes,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/services")
def dashboard_services():
    """
    서비스 상태
    - 중요 서비스 상태
    - health 결과
    """
    services_to_check = ["nginx", "sshd", "rsyslog", "python", "docker"]
    service_results = {
        name: get_service_status(name, OS_TYPE)
        for name in services_to_check
    }
    return {
        "services": service_results,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }



@router.get("/logs")
def dashboard_logs(
    file: Optional[str] = Query(default=None, description="로그 파일 경로"),
    lines: int = Query(default=10, ge=1, le=1000),
):
    """
    로그 조회
    - 최근 N줄
    - 파일별 tail
    - offset 또는 since 기반 조회
    """
    log_file = file or "/var/log/messages"
    logs = get_tail_log(log_file, lines, OS_TYPE)

    return {
        "logs": logs,
        "log_source": log_file,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }