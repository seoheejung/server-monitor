import psutil
import time
from typing import Iterable, List, Dict

from app.constants.ports import KNOWN_PORTS
from app.constants.windows import (
    WINDOWS_SYSTEM_PORTS,
    WINDOWS_ALLOWED_USER_PATHS,
    WINDOWS_SYSTEM_PROCS,
    WINDOWS_DEV_PROCS,
)
from app.constants.linux import (
    LINUX_CONTAINER_IGNORE_PROCS,
    BASE_ALLOWED_PREFIXES,
    CONDITIONAL_ALLOWED_PREFIXES,
)
from app.utils.env import is_container_environment

CACHED_KNOWN_PROCS = {} # DB에서 로드된 최적화 맵

def collect_processes(os_type: str) -> List[Dict]:
    """
    OS 공통 데이터 수집 
    
    psutil을 사용하여 OS 공통 프로세스 정보를 추출
    최대한 모든 OS에서 공통적으로 지원하는 속성만 선택적으로 수집
    """
    is_container = is_container_environment(os_type)
    processes = []

    # CPU 측정 초기화 (중요: 이전 측정값과의 차이를 계산하기 위함)
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # CPU 점유율 계산을 위한 최소한의 샘플링 시간
    time.sleep(0.1)

    # psutil.process_iter를 통해 실행 중인 모든 프로세스를 순회
    for proc in psutil.process_iter(attrs=[
        "pid",            # 프로세스 ID
        "name",           # 프로세스 이름
        "exe",            # 실행 파일 전체 경로
        "username",       # 실행 사용자 계정
        "create_time"     # 프로세스 시작 시간
    ]):
        try:
            # 🔒 PID 0 (System Idle Process) 무조건 제외
            if proc.pid == 0:
                continue

            info = proc.info # 수집된 기본 정보 딕셔너리
            name = (info.get("name") or "").lower()

            # 컨테이너 환경: 정책상 무시 프로세스 즉시 제외
            if is_container and name in LINUX_CONTAINER_IGNORE_PROCS:
                continue
            
            # oneshot을 쓰면 내부 데이터를 한 번에 가져와서 작업
            with proc.oneshot():
                try:
                    info["cpu_percent"] = proc.cpu_percent(None) # 실제 값
                except psutil.AccessDenied:
                    info["cpu_percent"] = None # 초기화

                try:
                    info["memory_percent"] = proc.memory_percent()
                except psutil.AccessDenied:
                    info["memory_percent"] = None

                info["ports"] = collect_ports(proc) # 네트워크 포트 정보 추가
                info["os_type"] = os_type
                processes.append(info)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 프로세스가 순회 중 종료되었거나, 접근 권한이 없는 경우 스킵
            continue

    return processes


def collect_ports(proc: psutil.Process) -> List[int]:
    """
    OS 공통 포트 수집
    특정 프로세스 객체(proc)가 점유하고 있는 네트워크 포트 수집
    
    시스템 전체 psutil.net_connections() 대신 특정 프로세스의 net_connections()만 조회
    root/admin 권한이 없으면 타 사용자의 프로세스 포트 정보는 누락될 수 있음 (AccessDenied 처리)
    """
    ports = set()

    try:
        # IPv4/IPv6 연결(inet)을 확인
        # psutil.connections로 시스템 전체를 뒤지지 않고 해당 프로세스의 소켓만 확인
        for conn in proc.net_connections(kind="inet"):
            # if conn.status == psutil.CONN_LISTEN and conn.laddr: # 열린 포트 (LISTEN)
            #     ports.add(conn.laddr.port) # 로컬 주소(laddr)의 포트 번호 저장
            if conn.laddr:
                ports.add(conn.laddr.port)
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        pass

    return sorted(list(ports))


def analyze_process(proc: Dict) -> Dict[str, List[str]]:
    """
    경고 판단 로직

    OS 환경이나 외부 라이브러리에 의존하지 않고, 오직 입력 데이터(dict)만 보고 위험 판단
    프로세스 정보를 바탕으로 위험 요소 분석
    """

    warnings =[]
    perf_warnings = []

    name = (proc.get("name") or "").lower()
    username = proc.get("username", "")
    memory = proc.get("memory_percent")
    ports = proc.get("ports") or []
    exe = proc.get("exe")
    os_type = proc.get("os_type")

    # [보안] 관리자/루트 권한 실행 여부 체크
    if os_type == "Windows":
        if username and username.upper() in (
            "SYSTEM",
            "NT AUTHORITY\\SYSTEM",
            "LOCAL SERVICE",
            "NETWORK SERVICE",
            "ADMINISTRATOR",
        ):
            if proc.get("pid") != 4:
                warnings.append("RUNNING_AS_ADMIN: 관리자 권한으로 실행 중")

    else: # Linux 계열
        if username == "root":
            warnings.append("RUNNING_AS_ADMIN: 관리자 권한으로 실행 중")

    # [보안] KNOWN_PORTS에 정의된 주요 서비스 포트 사용 여부 확인
    for port in ports:
        # Windows 시스템 기본 포트는 정상 동작으로 간주
        if (
            os_type == "Windows"
            and name in WINDOWS_SYSTEM_PROCS
            and port in WINDOWS_SYSTEM_PORTS
        ):
            continue

        if port in KNOWN_PORTS:
            warnings.append(f"PUBLIC_PORT({port}): KNOWN_PORTS 등록 주요 포트 사용 ({KNOWN_PORTS[port]})")
        elif port < 1024:
            warnings.append(f"SYSTEM_PORT({port}): 비표준 시스템 포트 개방")

    # [성능] 메모리 점유율이 과도한 경우 (임계치 20%)
    if isinstance(memory, (int, float)) and memory >= 20:
        perf_warnings.append(
            f"HIGH_MEMORY_USAGE: 메모리 점유율 높음 ({memory:.1f}%)"
        )

    # [보안] 실행 경로 (경로 개념 없는 프로세스는 검사 제외)
    # 경로 개념이 없는 시스템 프로세스는 검사 제외
    if os_type == "Windows" and name in WINDOWS_SYSTEM_PROCS:
        pass  # 경로 검사 안 함
    elif exe:
        if os_type == "Windows":
            # 개발 도구는 경로 경고 완화
            is_dev_proc = name in WINDOWS_DEV_PROCS
            if not is_dev_proc and not exe.startswith(WINDOWS_ALLOWED_USER_PATHS):
                warnings.append(
                    f"SUSPICIOUS_PATH: 비표준 경로에서 실행 중 ({exe})"
                )
        else:
            if exe.startswith(BASE_ALLOWED_PREFIXES):
                pass  # 정상
            elif exe.startswith(CONDITIONAL_ALLOWED_PREFIXES):
                warnings.append(
                    f"SUSPICIOUS_PATH: 조건부 허용 경로에서 실행 중 ({exe})"
                )
            else:
                warnings.append(
                    f"SUSPICIOUS_PATH: 비표준 경로에서 실행 중 ({exe})"
                )

    return {
        "warnings": warnings,
        "perf_warnings": perf_warnings,
    }


def sync_with_mongodb(db_data_list: Iterable[Dict], current_os: str):
    """
    MongoDB의 known_processes 컬렉션 데이터를 메모리로 동기화 로직
    
    우선순위:
    1. platform == common
    2. platform == 현재 OS
       -> 같은 name이면 OS 전용 설명이 common 설명을 덮어씀
    """

    global CACHED_KNOWN_PROCS
    current_os = (current_os or "").lower()
    temp_map = {}

    # 1. Common 데이터
    common_data = [
        d for d in db_data_list
        if isinstance(d.get("platform"), str)
        and d.get("platform").lower() == "common"
    ]

    # 2. OS 전용 데이터
    os_data = [
        d for d in db_data_list
        if isinstance(d.get("platform"), str)
        and d.get("platform").lower() == current_os
    ]

    # 데이터 가공 루프 (Common -> OS전용 순서로 실행하여 우선순위 확보)
    for item in (common_data + os_data):
        name = item.get("name")
        desc = item.get("description")

         # 핵심 방어
        if not isinstance(name, str) or not isinstance(desc, str):
            continue

        name = name.lower()
        
        policy = item.get("policy", {})
        normalized = {
            "description": desc,
            "policy": policy if isinstance(policy, dict) else {}
        }
        # Windows인 경우 확장자 대응용 가상 키 생성 (실제 DB 데이터는 하나지만 검색은 둘 다 되게)
        if current_os == "windows":
            name_no_ext = name.rsplit('.', 1)[0]
            temp_map[name_no_ext] = normalized
            temp_map[name] = normalized
            # 이미 .exe이면 중복 생성 방지
            if not name.endswith(".exe"):
                temp_map[f"{name_no_ext}.exe"] = normalized
        else:
            temp_map[name] = normalized
            
    CACHED_KNOWN_PROCS = temp_map


def explain_process(item: Dict | None, raw_name: str) -> str:
    """
    프로세스 설명(Explain)

    어려운 프로세스 명을 일반 사용자용 언어로 변환
    이미 최적화된 CACHED_KNOWN_PROCS를 사용하여 O(1)로 조회 
    """
    if not item:
        return f"미등록 프로세스 ({raw_name})"

    return item.get("description", f"미등록 프로세스 ({raw_name})")


def get_process_list(os_type: str) -> List[Dict]:
    """
    최종 조합 함수

    처리 흐름:
    1. 프로세스 수집
    2. 위험 분석 (warnings 생성)
    3. 상태 판단 (보안 정책 적용)
    4. UI 포맷 가공
    5. 위험도 기준 정렬
    """

    result = []

    # 1단계: 프로세스 수집
    raw_processes = collect_processes(os_type)

    # 2~4단계: 분석 + 상태 + 포맷
    for proc in raw_processes:
        # 프로세스 설명 및 정책
        raw_name = (proc.get("name") or "").lower()
        item = CACHED_KNOWN_PROCS.get(raw_name, {})
        if item:
            proc["explain"] = item.get("description", f"미등록 프로세스 ({raw_name})")
            proc["is_system"] = item.get("policy", {}).get("is_system", False)
        else:
            proc["explain"] = f"미등록 프로세스 ({raw_name})"
            proc["is_system"] = False

        # 위험 분석 수행
        analysis = analyze_process(proc)
        
        warnings = analysis["warnings"]
        perf_warnings = analysis["perf_warnings"]

        # 성능 경고를 기존 경고에 병합
        merged_warnings = warnings + [w for w in perf_warnings if w not in warnings]
        proc["warnings"] = merged_warnings
        proc["perf_warnings"] = perf_warnings

        # 상태 판단 (Case A/B/C 적용)
        build_status(proc)

        # UI 출력용 데이터 가공
        format_process(proc)

        result.append(proc)

    # 5단계: 위험도 기준 정렬
    result.sort(key=process_sort_key)

    return result

def build_status(proc: Dict):
    """
    보안 진단 가이드 기준으로 상태 결정

    Case A: KNOWN + Warning 없음 → ✅ 안전
    Case B: UNKNOWN + Warning 없음 → ⚠️ 경계
    Case C: Warning 존재
        - 치명 Warning → 🚨 위험
        - 일반 Warning → ⚠️ 주의
    """

    warnings = proc["warnings"]
    is_known = not proc["explain"].startswith("미등록")

    # 치명 Warning 정의 (정책 기준)
    CRITICAL_KEYWORDS = ("SUSPICIOUS_PATH", "RUNNING_AS_ADMIN")

    # Warning 분류
    critical = [w for w in warnings if any(k in w for k in CRITICAL_KEYWORDS)]
    normal = [w for w in warnings if w not in critical]

    # 정렬용 플래그 (치명 여부)
    proc["has_critical"] = bool(critical)

    # Case A
    if not warnings and is_known:
        proc["status_summary"] = "✅ 안전"
        proc["status_code"] = "OK"

    # Case B
    elif not warnings and not is_known:
        proc["status_summary"] = "⚠️ 미등록 프로세스"
        proc["status_code"] = "WARN"

    # Case C 
    elif critical:
        proc["status_summary"] = f"🚨 치명 경고 {len(critical)}건"
        proc["status_code"] = "DANGER"

    elif normal:
        proc["status_summary"] = f"⚠️ 일반 경고 {len(normal)}건"
        proc["status_code"] = "WARN"

    # 방어 코드 (이론상 도달하면 안됨)
    else:
        proc["status_summary"] = "⚠️ 상태 판별 불가"
        proc["status_code"] = "WARN"

def format_process(proc: Dict):
    """
    UI 출력용 데이터 가공

    - CPU / Memory 문자열 포맷팅
    - 사용자명 fallback 처리
    - 포트 리스트 요약
    """

    cpu_val = proc.get("cpu_percent")

    # CPU (% 단위 문자열)
    proc["cpu"] = f"{cpu_val:.1f}" if cpu_val is not None else "0.0"

    # 메모리 (% 단위 문자열)
    proc["memory"] = (
        f"{proc.get('memory_percent', 0):.1f}"
        if proc.get("memory_percent") is not None else "-"
    )

    # 사용자 정보
    proc["user"] = proc.get("username") or "-"

    # 포트 표시 (많으면 요약)
    ports = proc.get("ports", [])

    if len(ports) > 5:
        proc["display_ports"] = f"{ports[0]} 외 {len(ports)-1}건"
    elif ports:
        proc["display_ports"] = ", ".join(map(str, ports))
    else:
        proc["display_ports"] = ""

def process_sort_key(proc: Dict):
    """
    위험도 기반 정렬 기준

    우선순위:
    1. 치명 Warning 존재 여부 (최우선)
    2. Warning 개수 (많을수록 위)
    """

    return (
        not proc.get("has_critical", False),   # False(치명 있음) → 먼저
        -len(proc["warnings"]),     # Warning 개수 많은 순
    )