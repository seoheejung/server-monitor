KNOWN_PROCESSES = {
    # --- Linux Core & Shell ---
    "bash": "Bash: 리눅스 기본 대화형 쉘",
    "sh": "Shell: 표준 명령어 실행 환경",
    "init": "Init: 리눅스 최상위 프로세스 (PID 1)",
    "kthreadd": "Linux 커널 스레드 관리자",
    "systemd-journal": "Systemd 로그 수집 서비스",
    "systemd-udevd": "장치 관리 및 이벤트 처리 프로세스",

    # --- System Services (Linux) ---
    "rsyslogd": "rsyslogd: 시스템 로그 메시지 처리기",
    "dbus-daemon": "D-Bus: 프로세스 간 통신(IPC) 메시지 버스",
    "chronyd": "Chronyd: 네트워크 시간 동기화(NTP)",
    "polkitd": "Polkit: 시스템 권한 및 인증 정책 관리자",
    "agetty": "TTY 터미널 접속 관리자",
    "networkmanager": "NetworkManager: 네트워크 설정 관리자",

    # --- Web & App Runtimes (Linux Context) ---
    "uvicorn": "Uvicorn: FastAPI/Python ASGI 웹 서버",
    "apache": "Apache: 전통적인 웹 서버 (HTTPD)",
    "gunicorn": "Gunicorn: Python WSGI HTTP 서버",
    "nginx": "Nginx: 고성능 웹 서버 및 리버스 프록시",
    "python3": "Python3: 파이썬 3 런타임",
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
    "python": "Python: 스크립트 실행 환경",
    "node": "Node.js: JavaScript 서버 실행 환경",
    "java": "Java Runtime: JVM 기반 서비스",
    "php": "PHP: 서버 측 스크립트 언어 프로세스",
    "go": "Go Executable: Go 애플리케이션",
    "ruby": "Ruby: Rails 기반 서비스",

    # --- Infrastructure ---
    "docker": "Docker: 컨테이너 가상화 엔진",
    "dockerd": "Docker Daemon",
    "containerd": "Containerd 런타임",
    "kubelet": "Kubernetes 노드 관리자",
    "sshd": "SSH Daemon",
    "systemd": "Systemd 서비스 관리자",
    "crond": "Cron 작업 스케줄러",

        # --- Docker & Container ---
    "containerd-shim": "Containerd Shim: 컨테이너 실행 격리 레이어",
    "tini": "Tini: 컨테이너용 초소형 Init 프로세스",
    "sleep": "Sleep: 일시 중단 상태의 대기 프로세스",

    # --- Tools ---
    "grep": "Grep: 패턴 검색 도구",
    "ps": "PS: 프로세스 상태 확인 도구",
    "top": "Top: 실시간 시스템 리소스 모니터",
    "tail": "Tail: 파일 끝부분 출력 도구 (로그 확인용)",

    # --- Hyper-V / Virtualization ---
    "vmmemwsl": "WSL2 가상 머신 메모리 관리 프로세스",

    # --- Windows Core ---
    "system": "Windows 커널 시스템 프로세스",
    "system idle process": "CPU 유휴 시간 계산 프로세스",
    "registry": "Windows 레지스트리 커널 프로세스",
    "memcompression": "Windows 메모리 압축 관리 프로세스",
    "secure system": "가상화 기반 보안(VBS): 시스템의 핵심 자격 증명과 보안 데이터 보호",

    "smss.exe": "세션 관리자 서브시스템",
    "csrss.exe": "클라이언트/서버 런타임 서브시스템",
    "wininit.exe": "Windows 초기화 프로세스",
    "services.exe": "Windows 서비스 제어 관리자",
    "lsass.exe": "로컬 보안 인증 서비스",
    "lsaiso.exe": "LSA 격리 보안 프로세스",
    "winlogon.exe": "Windows 로그온 프로세스",

    "svchost.exe": "Windows 서비스 호스트",
    "spoolsv.exe": "프린터 스풀러 서비스",
    "audiodg.exe": "Windows 오디오 엔진",
    "wmiprvse.exe": "WMI Provider Host",
    "taskhostw.exe": "Windows 작업 호스트",
    "conhost.exe": "콘솔 창 호스트",

    "dllhost.exe": "COM Surrogate (썸네일·코덱 등 COM 객체 실행 호스트)",
    "fontdrvhost.exe": "Windows Font Driver Host (폰트 렌더링 격리 프로세스)",

    # --- Windows Security ---
    "msmpeng": "Windows Defender 실시간 백신 엔진",
    "mpdefendercoreservice": "Windows Defender 핵심 보안 서비스",
    "securityhealthservice": "Windows 보안 상태 모니터링 서비스",
    "securityhealthsystray": "Windows 보안 알림 트레이 프로세스",

    # ---UI / Shell / UWP ---
    "explorer.exe": "Windows 파일 탐색기",
    "dwm.exe": "바탕화면 창 관리자",
    "sihost.exe": "Shell Infrastructure Host",
    "runtimebroker.exe": "UWP 앱 권한 중개",
    "applicationframehost.exe": "UWP 앱 프레임 호스트",
    "startmenuexperiencehost.exe": "시작 메뉴 UI",
    "searchhost.exe": "Windows 검색 UI",
    "searchindexer.exe": "Windows 검색 인덱서",
    "textinputhost.exe": "텍스트 입력 관리자",
    "ctfmon.exe": "입력기/언어 바 서비스",
    "crossdeviceresume.exe": "Windows 크로스 디바이스 연속성 서비스",
    "shellhost.exe": "Windows Shell Host (UWP 쉘 컴포넌트)",
    "mspcmanagerservice.exe": "Microsoft PC Manager 서비스",

    "widgets.exe": "Windows 위젯 UI 프로세스",
    "widgetservice.exe": "Windows 위젯 백그라운드 서비스",

    ### --- dev ---
    "chrome.exe": "Google Chrome 브라우저",
    "code.exe": "Visual Studio Code",
    "powershell.exe": "PowerShell CLI",
    "dbeaver.exe": "DBeaver 데이터베이스 관리 도구 (DB 클라이언트)",

    "uvicorn.exe": "FastAPI / ASGI 개발 서버",
    "docker desktop.exe": "Docker Desktop",
    "com.docker.build.exe": "Docker 빌드 서비스",

    "virtualbox.exe": "VirtualBox 관리 UI",
    "virtualboxvm.exe": "VirtualBox 가상 머신",
    "vboxsvc.exe": "VirtualBox 서비스",
    "vboxnetdhcp.exe": "VirtualBox 네트워크 DHCP",

    "vmcompute.exe": "Hyper-V 가상 머신 연산 서비스",
    "vmmem.exe": "Hyper-V VM 메모리 관리자",
    "vmmemwsl.exe": "WSL2 가상 머신",
    "vmms.exe": "Hyper-V 가상 머신 관리 서비스",
    "vmwp.exe": "Hyper-V Virtual Machine Worker Process (가상 머신 실행 워커)",

    # --- WSL ---
    "wslservice.exe": "WSL 서비스",
    "wslrelay.exe": "WSL 네트워크/IPC 중계 프로세스",

    # --- 제조사 / 드라이버 (ASUS / AMD) ---
    "atiesrxx.exe": "AMD External Events Service",
    "atieclxx.exe": "AMD External Events Client",
    "rtkauduservice64.exe": "Realtek 오디오 서비스",
    "rtkbtmanserv.exe": "Realtek 블루투스 서비스",

    "asusoptimization.exe": "ASUS 시스템 최적화",
    "asusoptimizationstartuptask.exe": "ASUS 최적화 시작 작업",
    "asusappservice.exe": "ASUS 앱 서비스",
    "asusswitch.exe": "ASUS 시스템 스위치",
    "asushotkey.exe": "ASUS 단축키 서비스",

    "asussoftwaremanager.exe": "ASUS Software Manager (드라이버·유틸 관리)",
    "asussoftwaremanageragent.exe": "ASUS Software Manager Agent",
    "ascservice.exe": "ASUS System Control Interface Service",


    # --- Windows Driver / Device Framework ---
    "wudfhost.exe": "Windows User-Mode Driver Framework Host (USB·센서 등 사용자 모드 드라이버)",
    "wudfcompanionhost.exe": "WUDF 보조 호스트 프로세스 (디바이스 이벤트 처리)",
    "imfcore.exe": "Microsoft Input Framework Core",

    # --- Windows Management / WMI ---
    "unsecapp.exe": "WMI 비동기 콜백 처리 프로세스",
    "dashost.exe": "Device Association Framework Provider Host (장치 연결 관리)",
    "dataexchangehost.exe": "Windows 데이터 교환 호스트 (UWP 연동)",
    "backgroundtaskhost.exe": "UWP 백그라운드 작업 실행 호스트",

    # --- Input / Framework (IME, Media) ---
    "imf.exe": "Microsoft Input Method Framework (입력기 프레임워크)",
    "imfsrv.exe": "Microsoft Input Framework Service",
    "imftips.exe": "Microsoft 입력기 팁/보조 서비스",
    "imfelamsvc.exe": "Microsoft ELAM 입력기 보안 서비스",

    # --- Security / Auth ---
    "ngciso.exe": "Windows Hello 인증 격리 프로세스",

    # --- Browser / WebView ---
    "msedgewebview2.exe": "Microsoft Edge WebView2 (앱 내 웹 UI 렌더링)",
    "msrdc.exe": "Microsoft Remote Desktop Client",

    # --- Office ---
    "officeclicktorun.exe": "Microsoft Office Click-to-Run 업데이트 서비스",

    # --- Notes / UWP Apps ---
    "microsoft.notes.exe": "Microsoft Sticky Notes",

    # --- WSL ---
    "wsl.exe": "Windows Subsystem for Linux 실행 프로세스",
    "wslhost.exe": "WSL 가상 환경 호스트",

    # --- Manufacturer / OEM ---
    "asusosd.exe": "ASUS OSD (밝기·볼륨 등 화면 표시)",
    "amdppkgsvc.exe": "AMD Package Service (드라이버 패키지 관리)",

    # --- Security / Third-party ---
    "realtimeprotector.exe": "서드파티 실시간 보안/백신 보호 프로세스",
    "uninstallmonitor.exe": "프로그램 제거 감시 서비스",

    # --- Misc ---
    "appactions.exe": "Windows 앱 액션 처리 프로세스",
    "cagent.exe": "서드파티 에이전트 프로세스 (관리/보안 도구)",
    "notepad.exe": "Windows 메모장",

    # --- Applications ---
    "kakaotalk.exe": "카카오톡 메신저",
    "monitor.exe": "서드파티 모니터링/유틸리티 프로그램",
    "pet.exe": "서드파티 보조 실행 프로세스 (유틸/런처 계열)",

    # --- VirtualBox ---
    "vboxsds.exe": "VirtualBox Secure Data Service",

    # --- Windows Shell & Terminal ---
    "openconsole.exe": "Windows 콘솔 호스트: 명령줄 인터페이스의 출력창을 담당",
    "cmd.exe": "Windows 명령 프롬프트: 표준 커맨드 라인 인터프리터",
    "windowsterminal.exe": "Windows 터미널: 현대적인 다중 탭 터미널 에뮬레이터",
    "lockapp.exe": "Windows 잠금 화면: 시스템 잠금 및 로그인 배경 관리",

    # --- Drivers & Updates ---
    "nvdisplay.container.exe": "NVIDIA 디스플레이 컨테이너: 그래픽 드라이버 설정 및 관리",
    "microsoftedgeupdate.exe": "Microsoft Edge 업데이트: 브라우저 최신 버전 자동 유지",
}