import psutil
import time
from typing import List, Dict

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
    
    psutil.net_connections()보다 해당 프로세스 객체의 connections()를 쓰는 것이 훨씬 빠름
    root가 아니면 타 사용자의 프로세스 포트 정보는 누락될 수 있음 (AccessDenied 처리)
    """
    ports = set()

    try:
        # IPv4/IPv6 연결(inet)을 확인
        # psutil.connections로 시스템 전체를 뒤지지 않고 해당 프로세스의 소켓만 확인
        for conn in proc.connections(kind="inet"):
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
            warnings.append(f"PUBLIC_PORT({port}): {KNOWN_PORTS[port]} 포트 사용 중")
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


def sync_with_mongodb(db_data_list: List[Dict], current_os: str):
    """
    MongoDB의 known_processes 컬렉션 데이터를 메모리로 동기화 로직
    우선순위: OS별 전용 프로세스 > Common 프로세스
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
        # 기본 등록
        temp_map[name] = desc
        
        # Windows인 경우 확장자 대응용 가상 키 생성 (실제 DB 데이터는 하나지만 검색은 둘 다 되게)
        if current_os.lower() == "windows":
            name_no_ext = name.rsplit('.', 1)[0]
            name_with_exe = f"{name_no_ext}.exe"
            temp_map[name_no_ext] = desc
            temp_map[name_with_exe] = desc
            
    CACHED_KNOWN_PROCS = temp_map


def explain_process(proc:Dict) -> str:
    """
    프로세스 설명(Explain)

    어려운 프로세스 명을 일반 사용자용 언어로 변환
    이미 최적화된 CACHED_KNOWN_PROCS를 사용하여 O(1)로 조회
    """
    raw_name = (proc.get("name") or "").lower()

    # 딕셔너리에 있으면 설명 반환, 없으면 미등록 처리 (정책 반영)
    return CACHED_KNOWN_PROCS.get(raw_name, f"미등록 프로세스 ({raw_name})")


def get_process_list(os_type: str) -> List[Dict]:
    """
    최종 조합 함수 (정렬 기능 추가)
    
    1. 프로세스 정보 수집
    2. 위험 분석 및 해설 추가
    3. 위험도가 높은(경고가 많은) 프로세스를 상단으로 정렬
    """
    result = []

    # 1단계: 수집
    raw_processes = collect_processes(os_type)

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
            proc["status_code"] = "OK"
            # Case B : 정체는 모르지만 경고가 없는 경우
        elif risk_count == 0 and not is_known:
            proc["status_summary"] = "⚠️ 미등록 프로세스"
            proc["status_code"] = "WARN"
        else:
            # Case C: 경고가 존재하는 경우 (가장 첫 번째 경고를 대표로 표시하거나 개수 표시)
            main = proc["warnings"][0].split(":")[0]
            extra = risk_count - 1
            proc["status_summary"] = (
                f"🚨 {main} 외 {extra}건" if extra > 0 else f"🚨 {main}"
            )
            proc["status_code"] = "DANGER"

        # 4. UI 출력용 값 확정
        if proc["pid"] == 0:
            proc["cpu"] = "0.0"
        else:
            cpu_val = proc.get('cpu_percent', 0)
            # 논리적으로 한 프로세스가 전체 CPU 자원의 100%를 초과할 수 없으므로 제한
            proc["cpu"] = f"{min(cpu_val, 100.0):.1f}" if cpu_val is not None else "0.0"
        proc["memory"] = (
            f"{proc.get('memory_percent', 0):.1f}"
            if proc.get("memory_percent") is not None else "-"
        )
        proc["user"] = proc.get("username") or "-"

        ports_list = proc.get("ports", [])
        if len(ports_list) > 5:
            # 포트가 너무 많으면(크롬 등) 요약
            proc["display_ports"] = f"{ports_list[0]} 외 {len(ports_list)-1}건"
        elif len(ports_list) > 0:
            # 5건 이하면 콤마로 연결
            proc["display_ports"] = ", ".join(map(str, ports_list))
        else:
            proc["display_ports"] = " - "

        result.append(proc)

    # 3단계: 정렬 로직, 위험도 우선 정렬 (Case C가 항상 맨 위로)
    # warnings 리스트의 개수(len)를 기준으로 내림차순(reverse=True) 정렬
    result.sort(key=lambda x: len(x["warnings"]), reverse=True)
    return result