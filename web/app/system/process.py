import psutil
import os
import platform
from typing import List, Dict

OS_TYPE = platform.system()  # 'Windows' or 'Linux'

def collect_processes() -> List[Dict]:
    """
    OS 공통 데이터 수집 
    
    psutil을 사용하여 OS 공통 프로세스 정보를 추출
    최대한 모든 OS에서 공통적으로 지원하는 속성만 선택적으로 수집
    """
    processes = []

    # psutil.process_iter를 통해 실행 중인 모든 프로세스를 순회
    for proc in psutil.process_iter(attrs=[
        "pid",            # 프로세스 ID
        "name",           # 프로세스 이름
        "exe",            # 실행 파일 전체 경로
        "username",       # 실행 사용자 계정
        "cpu_percent",    # CPU 사용률 (%)
        "memory_percent", # 메모리 사용률 (%)
        "create_time"     # 프로세스 시작 시간
    ]):
        try:
            info = proc.info # 수집된 기본 정보 딕셔너리
            info["ports"] = collect_ports(proc.pid) # 네트워크 포트 정보 추가
            processes.append(info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # 프로세스가 순회 중 종료되었거나, 접근 권한이 없는 경우 스킵
            continue

    return processes


def collect_ports(pid: int) -> List[int]:
    """
    OS 공통 포트 수집

    특정 PID가 점유하고 있는 네트워크 포트 수집
    psutil.net_connections는 내부적으로 OS 명령어를 추상화하여 제공

    root 아니면 일부 누락 가능 → 정상
    """
    ports = set()

    try:
        # 모든 IPv4/IPv6 연결(inet)을 확인
        for conn in psutil.net_connections(kind="inet"):
            if conn.pid == pid and conn.laddr:
                ports.add(conn.laddr.port) # 로컬 주소(laddr)의 포트 번호 저장
    except psutil.AccessDenied:
        # 일반 사용자 권한으로는 다른 사용자의 포트 정보를 볼 수 없는 경우 발생
        pass

    return sorted(list(ports))


# 포트별 의미 및 보안 위협 설명
KNOWN_PORTS = {
    21: "FTP: 암호화되지 않은 파일 전송 (해킹 취약)",
    22: "SSH: 원격 접속 서비스",
    23: "Telnet: 암호화되지 않은 원격 접속 (매우 위험)",
    25: "SMTP: 메일 전송 프로토콜",
    53: "DNS: 도메인 이름 해석 서비스 (증폭 공격 주의)",
    80: "HTTP: 웹 서비스 (비암호화)",
    443: "HTTPS: 보안 웹 서비스",
    1433: "MSSQL: Microsoft SQL Server 데이터베이스",
    1521: "Oracle: Oracle 데이터베이스",
    3306: "MySQL: MySQL/MariaDB 데이터베이스",
    5432: "PostgreSQL: PostgreSQL 데이터베이스",
    6379: "Redis: 인메모리 데이터 저장소",
    8080: "HTTP-Proxy: 대체 웹 포트 (개발용/프록시)",
    9000: "FastCGI: PHP-FPM 등 어플리케이션 인터페이스",
    11211: "Memcached: 분산 메모리 캐싱 시스템",
    27017: "MongoDB: NoSQL 데이터베이스",
    3389: "RDP: Windows 원격 데스크톱 접속"
}

def analyze_process(proc:Dict) -> List[str]:
    """
    경고 판단 로직

    OS 환경이나 외부 라이브러리에 의존하지 않고, 오직 입력 데이터(dict)만 보고 위험 판단
    프로세스 정보를 바탕으로 위험 요소 분석
    """

    warnings =[]

    username = proc.get("username", "")
    memory = proc.get("memory_percent", 0)
    ports = proc.get("ports", [])
    exe = proc.get("exe") or ""

    # [보안] 관리자/루트 권한 실행 여부 체크
    if username in ("root", "SYSTEM", "Administrator"):
       warnings.append("RUNNING_AS_ADMIN: 관리자 권한으로 실행 중")

    # [보안] 주요 서비스 포트가 외부에 노출되어 있는지 확인
    for port in ports:
        if port in KNOWN_PORTS:
            # 포트 번호와 함께 정의된 설명을 추가
            warnings.append(f"PUBLIC_PORT({port}): {KNOWN_PORTS[port]}")
        elif port < 1024:
            # 정의되지 않았더라도 1024 미만 Well-known 포트는 주의 표시
            warnings.append(f"SYSTEM_PORT({port}): 비표준 시스템 포트 개방")

    # [성능] 메모리 점유율이 과도한 경우 (임계치 20%)
    if memory >= 20:
        warnings.append(f"HIGH_MEMORY_USAGE: 메모리 점유율이 높음 ({memory:.1f}%)")

    # [보안] 경로 의심 체크
    # Windows와 Linux의 표준 설치 경로가 다르므로 합집합 형태로 검사
    standard_paths = ("/usr", "/bin", "/opt", "C:\\Program Files", "C:\\Windows")
    if exe and not any(exe.startswith(p) for p in standard_paths):
        warnings.append("SUSPICIOUS_PATH: 비표준 경로에서 실행 중")

    return warnings


# 알려진 주요 프로세스에 대한 한글 설명
KNOWN_PROCESSES = {
    # --- Web & Proxy ---
    "nginx": "Nginx: 고성능 웹 서버 및 리버스 프록시",
    "apache": "Apache: 전통적인 웹 서버 (HTTPD)",
    "httpd": "Apache HTTP Server: 리눅스 표준 웹 서비스",
    "haproxy": "HAProxy: 부하 분산(Load Balancer) 솔루션",

    # --- Database & Cache ---
    "mysqld": "MySQL: 오픈소스 관계형 데이터베이스",
    "postgres": "PostgreSQL: 객체 관계형 데이터베이스(ORDBMS)",
    "sqlservr": "Microsoft SQL Server: 윈도우용 DB 엔진",
    "oracle": "Oracle DB: 대규모 기업용 데이터베이스",
    "redis-server": "Redis: 고속 인메모리 데이터 저장소",
    "memcached": "Memcached: 분산 메모리 캐싱 시스템",
    "mongod": "MongoDB: NoSQL 문서 지향 데이터베이스",

    # --- Runtime & Dev ---
    "python": "Python: 스크립트 실행 환경 (Django, Flask, AI 등)",
    "node": "Node.js: JavaScript 서버 실행 환경",
    "java": "Java Runtime: JVM 기반 서비스 (Spring, Tomcat 등)",
    "php": "PHP: 서버 측 스크립트 언어 프로세스",
    "go": "Go Executable: 컴파일된 Go 언어 애플리케이션",
    "ruby": "Ruby: Rails 프레임워크 기반 서비스",

    # --- Infrastructure & Tool ---
    "docker": "Docker: 컨테이너 가상화 엔진",
    "dockerd": "Docker Daemon: 컨테이너 관리 서비스",
    "containerd": "Containerd: 컨테이너 런타임 표준",
    "kubelet": "Kubernetes: 쿠버네티스 노드 관리자",
    "ssh": "SSH Client: 원격 접속 클라이언트",
    "sshd": "SSH Daemon: 외부 접속 허용 보안 쉘 서비스",
    "systemd": "Systemd: 리눅스 최상위 서비스 관리 프로세스",
    "crond": "Cron: 리눅스 주기적 작업 예약 실행기",

    # --- Windows Specific ---
    "lsass": "Local Security Authority: 사용자 인증/로그인 관리",
    "svchost": "Service Host: 여러 윈도우 서비스를 그룹화해 실행",
    "csrss": "Client Server Runtime: Win32 서브시스템 프로세스",
    "explorer": "Windows 탐색기: 파일 관리 및 데스크톱 UI",
    "spoolsv": "Print Spooler: 인쇄 대기열 관리",
    "taskmgr": "작업 관리자: 시스템 모니터링 도구",
    "conhost": "Console Window Host: 명령 프롬프트 지원 프로세스"
}


def explain_process(proc:Dict) -> str:
    """
    프로세스 설명(Explain)

    어려운 프로세스 명을 일반 사용자용 언어로 변환
    """
    name = proc.get("name", "").lower()

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
        proc["warnings"] = analyze_process(proc)
        
        # 3. 상태 요약 생성 (Case A, B, C 로직)
        if not proc["warnings"]:
            # Case A & B: 경고가 하나도 없는 경우
            proc["status_summary"] = "✅ 특이사항 없음"
        else:
            # Case C: 경고가 존재하는 경우 (가장 첫 번째 경고를 대표로 표시하거나 개수 표시)
            main_warning = proc["warnings"][0].split(":")[0] 
            proc["status_summary"] = f"⚠️ {main_warning} 외 {len(proc['warnings'])-1}건" if len(proc["warnings"]) > 1 else f"⚠️ {main_warning}"

        result.append(proc)


    # 3단계: 정렬 로직, 위험도 우선 정렬 (Case C가 항상 맨 위로)
    # warnings 리스트의 개수(len)를 기준으로 내림차순(reverse=True) 정렬
    result.sort(key=lambda x: len(x["warnings"]), reverse=True)
    return result
