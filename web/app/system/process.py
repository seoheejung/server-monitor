import psutil
import time
import os
import platform
from typing import List, Dict

from app.constants.ports import KNOWN_PORTS
from app.constants.processes import KNOWN_PROCESSES
from app.constants.windows import (
    WINDOWS_SYSTEM_PORTS,
    WINDOWS_ALLOWED_USER_PATHS,
    WINDOWS_SYSTEM_PROCS,
    WINDOWS_DEV_PROCS,
)

OS_TYPE = platform.system()  # 'Windows' or 'Linux'


def collect_processes() -> List[Dict]:
    """
    OS 공통 데이터 수집 
    
    psutil을 사용하여 OS 공통 프로세스 정보를 추출
    최대한 모든 OS에서 공통적으로 지원하는 속성만 선택적으로 수집
    """
    processes = []

    # CPU 측정 초기화 (중요)
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except Exception:
            pass

    time.sleep(0.1)  # 짧은 샘플링 시간

    # psutil.process_iter를 통해 실행 중인 모든 프로세스를 순회
    for proc in psutil.process_iter(attrs=[
        "pid",            # 프로세스 ID
        "name",           # 프로세스 이름
        "exe",            # 실행 파일 전체 경로
        "username",       # 실행 사용자 계정
        "create_time"     # 프로세스 시작 시간
    ]):
        try:
            # oneshot을 쓰면 내부 데이터를 한 번에 가져와서 작업
            with proc.oneshot():
                info = proc.info # 수집된 기본 정보 딕셔너리

                try:
                    info["cpu_percent"] = proc.cpu_percent(None) # 실제 값
                except psutil.AccessDenied:
                    info["cpu_percent"] = None # 초기화

                try:
                    info["memory_percent"] = proc.memory_percent()
                except psutil.AccessDenied:
                    info["memory_percent"] = None

                info["ports"] = collect_ports(proc) # 네트워크 포트 정보 추가
                info["os_type"] = OS_TYPE
                processes.append(info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # 프로세스가 순회 중 종료되었거나, 접근 권한이 없는 경우 스킵
            continue

    return processes


def collect_ports(proc: psutil.Process) -> List[int]:
    """
    OS 공통 포트 수집

    특정 PID가 점유하고 있는 네트워크 포트 수집
    psutil.net_connections는 내부적으로 OS 명령어를 추상화하여 제공

    root 아니면 일부 누락 가능 → 정상
    """
    ports = set()

    try:
        # IPv4/IPv6 연결(inet)을 확인
        # psutil.connections로 시스템 전체를 뒤지지 않고 해당 프로세스의 소켓만 확인
        for conn in psutil.connections(kind="inet"):
            if conn.status == psutil.CONN_LISTEN and conn.laddr: # 열린 포트 (LISTEN)
                ports.add(conn.laddr.port) # 로컬 주소(laddr)의 포트 번호 저장
    except psutil.AccessDenied:
        # 권한이 없거나 도중에 프로세스가 종료된 경우 빈 리스트 반환
        pass

    return sorted(list(ports))


def analyze_process(proc:Dict) -> List[str]:
    """
    경고 판단 로직

    OS 환경이나 외부 라이브러리에 의존하지 않고, 오직 입력 데이터(dict)만 보고 위험 판단
    프로세스 정보를 바탕으로 위험 요소 분석
    """

    warnings =[]
    perf_warnings = []

    name = (proc.get("name") or "").lower()
    username = proc.get("username", "")
    memory = proc.get("memory_percent", 0)
    ports = proc.get("ports", [])
    exe = proc.get("exe")
    os_type = proc.get("os_type")

    # [보안] 관리자/루트 권한 실행 여부 체크
    if username in ("root", "SYSTEM", "Administrator"):
        # Windows System(PID 4)는 정상
        if not (os_type == "Windows" and proc.get("pid") == 4):
            warnings.append("RUNNING_AS_ADMIN: 관리자 권한으로 실행 중")


    # [보안] 주요 서비스 포트가 외부에 노출되어 있는지 확인
    for port in ports:
        # ✅ Windows 기본 시스템 프로세스 포트 예외
        if (
            os_type == "Windows"
            and name in WINDOWS_SYSTEM_PROCS
            and port in WINDOWS_SYSTEM_PORTS
        ):
            continue

        if port in KNOWN_PORTS:
            warnings.append(f"PUBLIC_PORT({port}): {KNOWN_PORTS[port]}")
        elif port < 1024:
            warnings.append(f"SYSTEM_PORT({port}): 비표준 시스템 포트 개방")

    # [성능] 메모리 점유율이 과도한 경우 (임계치 20%)
    if memory >= 20:
        perf_warnings.append(
            f"HIGH_MEMORY_USAGE: 메모리 점유율 높음 ({memory:.1f}%)"
        )

    # [보안] 실행 경로 (경로 개념 없는 프로세스는 검사 제외)
    # 경로 개념이 없는 시스템 프로세스는 검사 제외
    if os_type == "Windows" and name in WINDOWS_SYSTEM_PROCS:
        pass  # 경로 검사 안 함
    elif exe:
        # 개발 도구는 경로 경고 완화
        is_dev_proc = os_type == "Windows" and name in WINDOWS_DEV_PROCS
        if os_type == "Windows":
            if not is_dev_proc and not exe.startswith(WINDOWS_ALLOWED_USER_PATHS):
                warnings.append(
                    f"SUSPICIOUS_PATH: 비표준 경로에서 실행 중 ({exe})"
                )
        else:
            if not exe.startswith(("/usr", "/bin", "/opt")):
                warnings.append(
                    f"SUSPICIOUS_PATH: 비표준 경로에서 실행 중 ({exe})"
                )


    return {
        "warnings": warnings,
        "perf_warnings": perf_warnings,
    }


def explain_process(proc:Dict) -> str:
    """
    프로세스 설명(Explain)

    어려운 프로세스 명을 일반 사용자용 언어로 변환
    """
    name = proc["name"].lower()

    # 단순 포함 여부(in)로 검사하여 버전이나 확장자가 붙어도 감지하게 함
    for key, desc in KNOWN_PROCESSES.items():
        if key in name:
            return desc
        
    return f"미등록 프로세스 ({name})"


def get_process_list() -> List[Dict]:
    """
    최종 조합 함수 (정렬 기능 추가)
    
    1. 프로세스 정보 수집
    2. 위험 분석 및 해설 추가
    3. 위험도가 높은(경고가 많은) 프로세스를 상단으로 정렬
    """
    result = []

    # 1단계: 수집
    raw_processes = collect_processes()

    # 2단계: 분석
    for proc in raw_processes:
        # 1. 정체 파악 (Case A vs B/C 결정 요소)
        proc["explain"] = explain_process(proc)
        
        # 2. 위험 분석 (진단 결과)
        analysis = analyze_process(proc)
        proc["warnings"] = analysis["warnings"]
        proc["perf_warnings"] = analysis["perf_warnings"]

         # verdict 판단은 보안 warnings만 사용
        is_known = not proc["explain"].startswith("미등록")
        risk_count = len(proc["warnings"])
        
        # 3. 상태 요약 생성 (Case A, B, C 로직)
        if risk_count == 0 and is_known:
            # Case A : 경고가 하나도 없는 경우
            proc["status_summary"] = "✅ 안전"
            # Case B : 정체는 모르지만 경고가 없는 경우
        elif risk_count == 0 and not is_known:
            proc["status_summary"] = "⚠️ 미등록 프로세스"
        else:
            # Case C: 경고가 존재하는 경우 (가장 첫 번째 경고를 대표로 표시하거나 개수 표시)
            main = proc["warnings"][0].split(":")[0]
            extra = risk_count - 1
            proc["status_summary"] = (
                f"🚨 {main} 외 {extra}건" if extra > 0 else f"🚨 {main}"
            )

        # 4. UI 출력용 값 확정
        proc["cpu"] = (
            f"{proc.get('cpu_percent', 0):.1f}"
            if proc.get("cpu_percent") is not None else "-"
        )
        proc["memory"] = (
            f"{proc.get('memory_percent', 0):.1f}"
            if proc.get("memory_percent") is not None else "-"
        )
        proc["user"] = proc.get("username") or "-"

        result.append(proc)


    # 3단계: 정렬 로직, 위험도 우선 정렬 (Case C가 항상 맨 위로)
    # warnings 리스트의 개수(len)를 기준으로 내림차순(reverse=True) 정렬
    result.sort(key=lambda x: len(x["warnings"]), reverse=True)
    return result
