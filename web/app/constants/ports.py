KNOWN_PORTS = {
    # 1. 🌐 원격 접속 및 관리 (외부 노출 시 매우 위험)
    22: "SSH (원격 접속 보안 셸)",
    23: "Telnet (보안 취약 원격 접속)",
    3389: "RDP (Windows 원격 데스크톱)",
    5631: "PCAnywhere (원격 제어 소프트웨어)",
    5900: "VNC (원격 화면 공유 서비스)",
    5985: "WinRM (Windows 원격 관리/HTTP)",
    5986: "WinRM (Windows 원격 관리/HTTPS)",

    # 2. 🗄️ 데이터베이스 및 저장소 (데이터 유출 위험)
    1433: "MSSQL (Microsoft SQL Server DB)",
    1521: "Oracle (Oracle DB)",
    3306: "MySQL (MySQL/MariaDB)",
    5432: "PostgreSQL (PostgreSQL DB)",
    6379: "Redis (인메모리 데이터 저장소)",
    7000: "Redis-Cluster (레디스 클러스터 통신)",
    9200: "Elasticsearch (검색 및 분석 엔진)",
    11211: "Memcached (분산 캐싱 시스템)",
    27017: "MongoDB (NoSQL 데이터베이스)",
    28017: "MongoDB-Web (몽고DB 웹 관리 인터페이스)",
    8500: "Consul (서비스 검색 및 설정 저장소)",
    26379: "Redis-Sentinel (레디스 고가용성 모니터링)",

    # 3. 💻 개발 도구 및 미들웨어 (내부망 전용 권장)
    2375: "Docker-API (도커 원격 제어/매우 위험)",
    3000: "Node.js/React (기본 개발 서버)",
    5000: "Flask/ASP.NET (웹 애플리케이션 프레임워크)",
    8000: "Django/Common-Dev (일반적인 개발 웹 서버)",
    8080: "Java-Spring/Tomcat (기본 웹 서비스 포트)",
    8081: "Jenkins/Nexus (지속적 통합 및 저장소 서버)",
    8888: "Jupyter Notebook (데이터 분석 도구/프록시)",
    9000: "FastCGI (애플리케이션 인터페이스)",
    9090: "Prometheus (시스템 모니터링 서버)",
    9092: "Kafka (메시지 스트리밍 플랫폼)",
    15672: "RabbitMQ (메시지 브로커 관리 화면)",
    1883: "MQTT (IoT 메시징 프로토콜)",
    35729: "LiveReload (개발 중 자동 새로고침 포트)",
    61613: "ActiveMQ (메시지 브로커 STOMP 포트)",

    # 4. 📂 인프라 및 파일 공유 (랜섬웨어 취약 포트)
    21: "FTP (암호화 미지원 파일 전송)",
    111: "RPCBind (RPC 서비스를 포트 번호에 매핑)",
    135: "RPC (원격 프로시저 호출)",
    137: "NetBIOS (이름 서비스)",
    139: "NetBIOS (세션 서비스)",
    445: "SMB (윈도우 파일/프린터 공유)",
    2049: "NFS (네트워크 파일 시스템)",

    # 5. 📧 기본 웹 및 시스템 서비스
    25: "SMTP (메일 발송 서비스)",
    53: "DNS (도메인 주소 해석/증폭 공격 주의)",
    80: "HTTP (암호화되지 않은 웹 트래픽)",
    161: "SNMP (네트워크 장비 모니터링)",
    443: "HTTPS (보안 웹 트래픽)",
    8443: "HTTPS-Alt (대체 보안 웹 포트)",
    
    # 6. ⚓ 클라우드 및 컨테이너 (인프라 노출 위험)
    2379: "etcd (분산 키-값 저장소/K8s 핵심 데이터)",
    6443: "Kubernetes-API (쿠버네티스 API 서버)",
    10250: "Kubelet-API (쿠버네티스 노드 관리)",
    30000: "K8s-NodePort (쿠버네티스 서비스 노출 시작 포트)",

    # 7. 🤖 AI 및 신기술 (최신 보안 위협)
    7860: "Gradio/Stable-Diffusion (AI 모델 인터페이스)",
    11434: "Ollama (로컬 AI 모델 서비스)",
    8501: "Streamlit (데이터 시각화/AI 대시보드)",
    
    # 8. 🛠️ 보안 위협 및 침투 테스트 도구 (탐지 시 즉시 조치 필요)
    1080: "SOCKS-Proxy (익명 프록시 포트)",
    3128: "Squid-Proxy (웹 프록시 캐시 서버)",
    4444: "Metasploit/Malware (해킹 도구/백도어 기본 포트)",
    5555: "ADB (안드로이드 디버그 브릿지/원격 제어 위험)",
    6667: "IRC (채팅 프로토콜/보트넷 명령 제어 악용)",
    8008: "HTTP-Alt (대체 웹 서비스/일부 악성코드 활용)",
    9999: "Urchin/Malware (일부 백도어 프로그램용 포트)",

    # 9. ⚠️ 신규 추가: 공격용 인프라 및 가상화 취약 포트
    31337: "Back-Orifice (유명 해킹 툴/백도어)",
    3333: "Crypto-Miner (암호화폐 채굴 풀 통신/Stratum)",
    5554: "Malware-C2 (일부 봇넷 명령 제어 포트)",
    8082: "Web-Server (H2 데이터베이스 콘솔/취약점 다수)",
    9001: "Tor-Relay (토어 네트워크 우회 통로)",
    50000: "Jenkins-Agent (젠킨스 노드 연결/관리자 권한 탈취 위험)",
}