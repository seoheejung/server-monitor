WINDOWS_SYSTEM_PORTS = {
    # --- 핵심 네트워킹 ---
    135, 137, 138, 139, 445,   # RPC, NetBIOS, SMB
    5357, 5358,                # WSD (장비 탐색)

    # --- 서비스 발견 및 해석 ---
    53,                        # DNS
    1900,                      # SSDP (UPnP 장치 검색)
    5353,                      # mDNS (애플 기기/네트워크 프린터)
    5355,                      # LLMNR (로컬 이름 해석)

    # --- 시스템 관리 및 인증 ---
    88,                        # Kerberos (도메인 환경 인증)
    123,                       # NTP (시간 동기화)
    5985, 5986,                # WinRM (윈도우 원격 관리)
}


WINDOWS_ALLOWED_USER_PATHS = (
    "C:\\Users",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\Windows",
    "C:\Windows\System32\\"
)

WINDOWS_SYSTEM_PROCS = {
    # 커널 및 특수 프로세스 (경로가 없음)
    "system", "registry", "memcompression", 
    "vmmemwsl", "vmmem", # WSL 가상 메모리 프로세스

    # 세션 및 초기화 (윈도우 부팅 필수)
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    
    "svchost.exe",      # 서비스 호스트
    "services.exe",     # 서비스 관리자
    "lsass.exe",        # 로컬 인증
}

WINDOWS_DEV_PROCS = {
    # --- 에디터 및 IDE (UI 기반 개발 도구) ---
    "code.exe",           # Visual Studio Code
    "idea64.exe",         # IntelliJ IDEA
    "pycharm64.exe",      # PyCharm
    "visualstudio.exe",   # Visual Studio (C++, C# 등)

    # --- 런타임 및 언어 (실제 포트를 열고 코드를 실행하는 주범) ---
    "node.exe",           # Node.js / React / Vue 개발 시 필수
    "python.exe",         # Python / Django / Flask / AI 모델 실행
    "java.exe",           # Spring Boot / Android 개발
}