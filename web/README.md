# server-monitor web

**Rocky Linux 서버의 상태를 웹으로 확인하기 위한 서버 모니터링 프로젝트**

> 개발 → Linux 이식 → 운영 확장을 고려한 구조 중심 문서


###  핵심 기능
1. 기본 모니터링 (1차)
   - 시스템 리소스 시각화
     - CPU, RAM, Disk 사용량을 픽셀 스타일 대시보드로 실시간 확인
   - 하이브리드 서비스 모니터링
     - Linux: systemctl 기반 서비스 상태 감지
     - Docker / Native: psutil 기반 프로세스 상태 분석
     - 로그 스트리밍: 시스템 및 서비스 로그를 웹 콘솔에서 즉시 확인
2. 프로세스 보안 분석 (2차)
   - 실행 중 프로세스 상세 분석 (Cross Platform)
     - root/SYSTEM 실행 여부, 비표준 경로, 위험·시스템 포트 점유 자동 진단
   - Explain & Warning
     - 각 프로세스의 역할과 현재 위험 요소를 사용자가 이해 가능한 언어로 설명
     - 정상 / 주의 / 위험 상태를 도트 기반 콘솔 UI로 시각화
3. 운영 제어 & 정책 관리 (3차)
   - 정책 기반 프로세스 관리
     - MongoDB 연동으로 KNOWN_PROCESSES 및 보호 정책 중앙 관리
   - 안전한 프로세스 종료
     - 시스템 프로세스 보호
     - Soft Kill → Hard Kill 단계적 종료 로직
   - 운영 확장 기반
     - 운영자 개입 없이 정책에 따른 판단·제어 구조 확보
---
<br>

## 프로젝트 구조

```
web/
├── app/
│   ├── main.py          # FastAPI 엔트리 (URL 및 서버 설정)
│   ├── database/                  # DB 연결
│   ├── constants/       # 포트 / 프로세스 정책
│   │   ├── ports.py
│   │   ├── processes.py
│   │   └── windows.py
│   ├── system/          # 서버 정보 수집 코드 모음
│   │   ├── cpu.py       # CPU 사용량
│   │   ├── memory.py    # 메모리 사용량
│   │   ├── disk.py      # 디스크 사용량
│   │   ├── uptime.py    # 서버 업타임
│   │   ├── service.py   # 서비스 상태 (systemctl)
│   │   ├── log.py       # 로그 tail 기능
│   │   └── process.py   # 프로세스 분석 (확장) 
│   ├── templates/       # 웹 화면(HTML)
│   │   └── dashboard.html
│   └── static/          # 정적 파일
│       └── style.css
├── .env                 
├── .gitignore           
├── requirements.txt     # 의존성 패키지 목록
├── run.py               # 서버 통합 실행 스크립트
└── README.md
```
### 프로젝트 진행 흐름
#### 🗂️ Windows 개발  → Linux 이식  → 운영 확장

---
<br>

## [1단계] Windows에서 FastAPI 서버 실행 확인
### 1. 가상환경 생성
```
python -m venv venv
```
### 2. 보안 설정
- Windows PowerShell은 보안 때문에 기본적으로 .ps1 스크립트 실행을 막아둠
- Activate.ps1는 PowerShell 스크립트 그래서 가상환경 활성화가 차단됨
- powerShell을 관리자 말고 그냥 그대로 실행 후 명령어 입력
    ```
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    ```

 | 항목           | 설명             |
 | ------------ | -------------- |
 | CurrentUser  | 내 계정에만 적용      |
 | RemoteSigned | 인터넷에서 받은 것만 제한 |
 | 로컬 venv 스크립트 | 실행 가능          |

### 3. 가상환경 활성화 (Windows PowerShell)
```
venv\Scripts\activate
```
- 프롬프트에 (venv) 뜨면 OK

### 4. 패키지 설치 (Windows)
```
pip install fastapi uvicorn psutil jinja2

# 미리 정해둔 라이브러리 목록 사용 가능
# pip install -r requirements.txt 

# 확인
pip list
```
- FastAPI : 웹 서버(REST API)를 만들기 위한 핵심 프레임워크
- Uvicorn : FastAPI를 실제로 실행해 주는 웹 서버 프로그램
- psutil : 리눅스/윈도우 서버 상태(CPU, 메모리 등)를 가져오는 라이브러리
- Jinja2 : Python 데이터를 HTML로 바꿔주는 템플릿 엔진

```
[ 서버 상태 ]
    ↓ psutil
[ Python 코드 ]
    ↓ FastAPI
[ HTML 생성 ]
    ↓ Jinja2
[ 웹 서버 실행 ]
    ↓ Uvicorn
[ 브라우저 ]
```

### 5. app/main.py 작성
```
from fastapi import FastAPI

app = FastAPI(title="server-monitor")

@app.get("/")
def root():
    return {"message": "server-monitor running"}
```

### 6. FastAPI 서버 실행 (Windows)
```
uvicorn app.main:app --reload

# 성공하면 콘솔에 입력
Uvicorn running on http://127.0.0.1:8000
```

### 7. 브라우저 확인 (http://127.0.0.1:8000/)
```
{"message":"server-monitor running"}
```

<br>

### * FastAPI 서버를 실행할 때마다 가상환경(venv) 실행
```
[ 내 PC 전체 Python ]
        |
        |  (venv 켜기)
        v
[ server-monitor 전용 Python ]
```
- venv를 안 켜면 FastAPI가 존재하지 않음

#### * 실행 루틴
```
# 1. 프로젝트 폴더 이동
cd web

# 2. 가상환경 활성화
venv\Scripts\activate

# 3. 서버 실행
uvicorn app.main:app --reload
```

#### * 서버는 계속 켜져 있어야 하는데?
> 운영 서버(Linux) 에서는 다름.

1. 지금 (Windows 개발 단계)
   - 개발자가 직접 실행
   - 콘솔 껐다 켜면 다시 실행
   - 👉 venv 매번 켬

2. 나중 (Rocky Linux 운영)
   - systemd / supervisor / docker
   - 실행 스크립트에 venv 경로를 명시
   - 운영자가 직접 activate 안 함
       ```
       /opt/server-monitor/venv/bin/uvicorn app.main:app
       ```
   - 👉 운영에서는 자동

---
<br>

## [2단계] API 구현
### 1. 시스템 정보 수집 (CPU)
   - psutil 중 가장 단순 (OS 권한 문제 없음)
   - 정확도 확보: psutil.cpu_percent(interval=1)를 사용하여 1초간의 평균 부하 측정
   - Windows와 Linux에서 동일한 API로 동작하여 개발 편의성 확보

### 2. 리소스 가공 (메모리, 디스크, 구동 시간)
   - 메모리: psutil.virtual_memory()
     - 전체(Total), 사용량(Used), 퍼센트(Percent) 추출
   - 디스크: psutil.disk_usage('/')
     - OS별 루트 경로 분기 처리
       - Linux : `/`
       - Windows : `C:\\`
   - 구동 시간: psutil.boot_time()
     - 부팅 시점 타임스탬프와 datetime.now()의 차이를 계산
     - timedelta를 사용하여 D+H:M 형태의 사용자 친화적 문자열로 가공

### 3. 서비스 상태
  - 운영체제에 따른 분기 처리 필요
    - Windows: `platform` 체크를 통해 미지원 메시지 출력 및 예외 처리
    - Linux (Host): `systemctl is-active` 명령어를 우선 사용하여 OS 레벨의 표준 상태 수집
    - Docker (Container): `systemctl`이 없는 환경은 `psutil.process_iter`로 프로세스명 검색
  - 모니터링 대상 서비스 정의 (services_to_check)
    - 네트워크/인프라: nginx (웹 서비스), sshd (원격 관리)
    - 시스템 운영: rsyslog (로그 관리), docker (가상화 서비스)
    - 실행 환경: python (백엔드 구동 환경)

### 4. 로그 수집 (tail)
   - 대용량 로그 파일 전체를 읽지 않고, 파일 끝(EOF)에서부터 최근 10~20줄만 추출하는 tail 로직 구현
   - `/var/log` 접근 시 발생할 수 있는 **PermissionError**를 `try-except`로 처리하여 서버가 중단되지 않게 방어 코드 작성

### 5. 대시보드
  - Jinja2 템플릿을 활용한 화면 분리
      ```
      Python 데이터 → Jinja2 → HTML
      ```
  - UI 컨셉
      ```
      [ 서버 상태 대시보드 ]

      CPU 사용률: 23%
      RAM 사용량: 5.2GB / 16GB
      Disk 사용량: 40%

      서비스 상태
      - nginx: active
      - docker: active

      최근 로그
      --------------------------------
      [INFO] ...
      [WARN] ...

      실행 중인 프로세스

      ```
      - Retro / Pixel Server Console
      - 도트 배경 → 서버 콘솔 느낌
      - 픽셀 폰트 → 시스템 모니터링 감성
      - 굵은 테두리 → 상태판 느낌
      - box-shadow → 픽셀 카드 연출
      - 리소스 수치에 따라 good/warn/bad CSS 클래스 자동 부여.
      - 서비스 상태(active, failed)에 따라 도트 색상 변경.

---
<br>

## [2-1단계] 추가 기능 (2차) : 프로세스 분석 & 보안 관점 모니터링

### 실행 중인 프로세스 분석 기능 🔍 (Cross Platform)
> 단순히 CPU/메모리 수치만 보여주는 모니터링이 아니라,   
> “현재 서버에서 무엇이 돌아가고 있고, 이게 위험한지 아닌지”를 설명하는 것을 추가  

### 1. 수집 정보
- Windows / Linux 공통으로 정보 수집
- psutil 라이브러리 기반으로 OS 의존성 최소화
  
| 항목      | 설명                      | 코드 대응 키 |
| ------- | ----------------------- | --------------- |
| 프로세스명   | 실행 중인 프로그램 이름     | name     |
| PID     | 프로세스 고유 ID              | pid     |
| 실행 경로   | 실제 실행 파일 위치         | exe     |
| CPU 사용률 | 프로세스별 CPU 점유율          | cpu_percent     |
| 메모리 사용률 | 프로세스별 메모리 점유율      | memory_percent     |
| 열린 포트   | 해당 PID가 점유한 네트워크 포트 리스트          | ports     |
| 실행 사용자  | 실행 주체 (root / SYSTEM / Administrator) | username     |
| 시작 시간   | 프로세스 생성 시점          | create_time     |

```
process.py
├── collect_processes()   # OS 공통: psutil 기반 프로세스 수집
├── collect_ports(pid)    # OS별 분기: PID 기준 포트 수집
├── analyze_process(proc) # 위험 요소(Warning) 판단
├── explain_process(proc) # 프로세스 역할 설명
└── get_process_list()    # 수집 + 분석 + 설명 통합
```

### Rocky Linux(Linux) 이식 시 주의사항 업데이트 💡 
1. 권한 기준
   - Windows: SYSTEM, Administrator
   - Linux: root
2. 표준 경로
   - /usr, /bin, /opt 외
   - 필요 시 /var/lib, /tmp 등 허용 경로 추가 가능
3. 포트 수집 권한
   - 일반 사용자 실행 시 타 사용자 프로세스의 포트 수집 불가 가능
   - 정확한 분석을 위해 `sudo` 실행 여부 검토 필요
   - Linux 환경에서 모든 프로세스의 포트 정보를 수집하려면 python 실행 시 `sudo 권한`이 필요하거나, `net-tools` 패키지 설치 필요
   
<br> 

### 2. 위험 요소(Warning) 자동 분석
- 각 프로세스에 대해 보안/운영 관점 경고 자동 판단
- **정상 동작**과 **주의 필요**를 사용자가 바로 이해 가능

| 경고                | 의미                 | 판단 기준        | 
| ----------------- | ------------------ |------------------ |
| RUNNING_AS_ROOT   | root/관리자 권한으로 실행 중 | `username`이 root, SYSTEM, Administrator |
| PUBLIC_PORT(n)    | 위험/주요 포트 외부 노출 | `KNOWN_PORTS`에 정의된 포트 점유 시 설명 포함 |
| SYSTEM_PORT(n)    | 비표준 시스템 포트 사용 | 1024 미만 포트 중 정의되지 않은 포트 사용 시 |
| HIGH_MEMORY_USAGE | 메모리 과다 사용    | `memory_percent ≥ 20%` |
| SUSPICIOUS_PATH   | 비정상 경로에서 실행    | OS별 표준 경로 외 실행 |

> ⚠️ Windows System(PID 4) 및 커널/가상 프로세스는 오탐 방지를 위해 분석 제외

<br>

### 3. 프로세스 설명(Explain) 및 보안 진단 가이드
- 프로세스의 **역할(Explain)**과 **현재 위험 상태(Warning)**를 함께 표시
- **무슨 프로세스인지 + 지금 안전한지**를 동시에 전달

```
nginx
 └ 역할: 웹 서버 (외부 HTTP 요청 처리)
 └ 상태: ⚠️ PUBLIC_PORT(80) – 비암호화 포트 노출

redis-server
 └ 역할: 인메모리 데이터 저장소
 └ 상태: ⚠️ PUBLIC_PORT(6379) – 외부 접근 주의
```

### 보안 진단 가이드 로직 🔐
1. KNOWN_PROCESSES에 존재 + Warning 없음 → ✅ 안전
2. KNOWN_PROCESSES에 없음 + Warning 없음 → ⚠️ 경계 (사용자 확인 필요)
3. Warning이 하나라도 존재 → 🚨 위험 / 주의 (즉시 점검 권장)

```
CASE A: 정체는 알고 있고, 위험도 없는 경우
- Process: explorer.exe (윈도우 탐색기)
- Explain: KNOWN_PROCESSES에 있음 → "Windows 탐색기: 파일 관리 및 데스크톱 UI"
- Warnings: 권한/경로/포트 모두 정상 → "✅ 특이사항 없음"
- 결과: ✅ 정상 동작

CASE B: 정체는 모르지만, 위험도 없는 경우
- Process: my_custom_tool.exe (내가 직접 만든 도구)
- Explain: KNOWN_PROCESSES에 없음 → "❓ 알 수 없는 사용자/시스템 프로세스"
- Warnings: 권한/경로/포트 모두 정상 → "✅ 특이사항 없음"
- 결과: ⚠️ 경계 (용도만 확인하면 됨)

CASE C: 정체도 모르고, 위험도 있는 경우 (최우선 대응)
- Process: hacker_tool.exe
- Explain: KNOWN_PROCESSES에 없음 → "❓ 알 수 없는 사용자/시스템 프로세스"
- Warnings: 관리자 권한, 비표준 경로 등 발견 → "⚠️ SUSPICIOUS_PATH"
- 결과: 🚨 즉시 조치 필요
```

<br>

### 4. 도트 기반 콘솔 UI (Retro Server Dashboard)
- 상태 표현 규칙
  
| 상태 | 도트 |
| -- | -- |
| 정상 | 🟢 |
| 주의 | 🟡 |
| 위험 | 🔴 |

- 콘솔 스타일 예시
```
🟢 nginx   PID 1324   PORT 80,443
🟡 redis   PID 2211   PORT 6379
🔴 mysql   PID 998    PORT 3306
```

---
<br>

## [2-2단계] 추가 기능 (3차) : MongoDB 연동 & 프로세스 종료

### 1. MongoDB
- 설계 (KNOWN_PROCESSES 전용)
   - KNOWN_PROCESSES = 판단 기준 사전
   - 실행 중 프로세스 저장 ❌
   - KNOWN_PROCESSES에 정의된 프로세스만 활용
   - 매칭 실패 시 → Unknown Process 로 처리 (DB 저장 ❌)

<br>

- `known_processes` 컬렉션 구조
    ```json
    {
        "_id": ObjectId,

        "name": "svchost.exe",
        "platform": "windows",
        "category": "system_core",           // 분류용
        "description": "Windows 서비스 호스트",

        "policy": {
        "is_system": true, 
        "terminatable": false, 
        "reason": "Windows core service"
        },

        "tags": [
            "core",
            "protected",
            "windows"
        ],
        "created_at": Date
    }
    ```
    - 구설명
      - name: 프로세스 이름
      - platform: 운영체제 (예: windows | linux | common)
      - category: 분류 (예: kernel | system_core)
      - description: 프로세스에 대한 설명
      - policy: 시스템 여부(is_system), 종료 가능 여부(terminatable), 사유(reason)를 포함하는 정책 객체
      - tags: 관련 키워드 리스트
    - 플랫폼 처리 방식
    - platform = common (Windows / Linux 공통 적용)
    - 조회 우선순위
      1. (name, platform=os)
      2. (name, platform=common)

- 인덱스 설계
    ```js
    db.known_processes.createIndex(
        { name: 1, platform: 1 },
        { unique: true }
    )
    ```
    - 복합 인덱스 생성 (name: 1, platform: 1)
    - unique=True로 설정하여 중복 데이터 방지

- 데이터 변환 및 분류 규칙
  1. Platform 판별
     - .exe가 이름에 있거나 설명에 windows가 포함되면: windows
     - docker나 nginx가 이름에 포함되면: common
     - 그 외의 경우: linux
  2. System 여부 (is_system)
     - 설명(desc)에 `"시스템", "커널", "core", "보안", "관리자"` 중 하나라도 포함되면 true
  3. Policy 설정
     - `is_system true`: terminatable: false, reason: "System Core"
     - `is_system false`: terminatable: true, reason: "User Application"
  4. category
     - kernel / core: 운영체제 부팅 및 유지에 필수적인 경우 (init, kthreadd)
     - database: 데이터 저장 및 관리 목적 (mysqld, postgres)
     - network-service: 네트워크 연결, 원격 접속 및 시간 동기화 관리 (sshd, networkmanager)
     - system-service: 백그라운드에서 시스템 기능 보조 및 로그/권한 관리 (rsyslogd, polkitd)
     - monitoring: 시스템 리소스 상태 감시 및 프로세스 활동 추적 (top, htop)
     - container-runtime: 컨테이너의 격리 실행 및 생명주기 관리 레이어 (containerd, tini)
     - web-server: 웹 요청 처리 및 라우팅 (nginx, apache)
     - runtime: 프로그래밍 언어 실행 환경 (python, node)
     - infrastructure: 가상화 및 클러스터 관리 (docker, kubelet)
     - system-utility: 단순 도구 및 명령어 (grep, ps, tail)
  5. 기타 필드
     - 기본적으로 "general"로 설정
     - tags는 [platform, "auto-imported"] 구성
     - created_at 필드 추가 (ISO 8601 형식)

<br>

- mongoDB 설치
  - Window에서 도커로 설치
    ```
    docker run -d --name mongodb -p 27017:27017 mongo
    ```
  - 도커 컨테이너로 실행 중인 Rocky Linux 환경
    ```
    docker exec -it rocky_server /bin/bash
    ```
    - MongoDB 공식 레포지토리 등록
        ```
        # 레포지토리 파일 생성
        cat <<EOF | tee /etc/yum.repos.d/mongodb-org-7.0.repo
        [mongodb-org-7.0]
        name=MongoDB Repository
        baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/7.0/x86_64/
        gpgcheck=1
        enabled=1
        gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
        EOF
        ```
    - MongoDB 패키지 설치
        ```
        dnf install -y mongodb-org

        # 데이터 디렉토리 생성
        mkdir -p /data/db
        # MongoDB 실행 (백그라운드)
        mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db

        systemctl start mongod
        systemctl enable mongod
        ```

<br>

### 2. 프로세스 종료
>  Kill / Terminate가 아니라 종료, 정리, 리소스 해제

#### (참고) PC Manager
- 상태 기반 앱 정리 도우미
- PC Manager의 판단 기준 (추정이 아니라 실제 UX 기준)
  - 사용자 앱
  - 백그라운드 앱
  - 장시간 미사용
  - 메모리 과다 사용
  - 시스템 필수 프로세스 제외

    ```
    📌 정리 가능 항목
    - Chrome (메모리 1.2GB)   [종료]
    - Node App (포트 3000)    [종료]

    🔒 시스템 프로세스
    - lsass.exe
    - svchost.exe
    ```

<br>

1. 종료 대상 구분
    | 구분        | Windows                    | Linux                   |
    | --------- | -------------------------- | ----------------------- |
    | **종료 대상** | explorer.exe 하위 프로세스       | 로그인 사용자 UID 소유          |
    |           | 사용자 계정 소유                  | TTY / graphical session |
    |           | GUI 세션에 속함                 | `/home/*` 경로 실행 파일      |
    |           | UWP / Win32 사용자 앱          |                         |
    | **제외 대상** | SESSION 0                  | UID 0 (root)            |
    |           | SYSTEM / LOCAL SERVICE     | systemd / daemon        |
    |           | Windows signed core binary | `/usr/lib/systemd`      |
    |           | svchost 계열                 |                         |

<br>

2. 프로세스 종료 판단 플로우
    ```
    [프로세스 수집]
        ↓
    [KNOWN_PROCESSES Mongo 조회]
        ↓
    [process_rules 조회]   (있다면)
        ↓
    [policy.is_system 확인]
        ↓
    [policy.terminatable 결정]
        ↓
    [UI 종료 버튼 활성화]
    ```
    - PID / UID / SESSION 판단은 실시간 데이터
    - 이름 기준 정책만 `MongoDB`

<br>

3. 설계안 (Soft Kill → Hard Kill)
    ```
    [사용자 종료 클릭]
        ↓
    [MongoDB known_processes 재조회]
        ↓
    [terminatable == true ?]
        ↓
    [Soft 종료]
        ↓ (5초)
    [Hard 종료]
        ↓
    [종료 결과 즉시 반영]
    ```
    **설계 원칙**
    - UI 상태를 신뢰하지 않음
    - 종료 직전 항상 DB 재검증
    - Hard Kill은 최후 수단

4. OS별 실제 종료 방식
    | 단계               | Windows                  | Linux                          |
    | ---------------- | ------------------------ | ------------------------------ |
    | **1차 종료 (Soft)** | `taskkill /PID <pid>`    | `SIGTERM`                      |
    | **대기**           | 정상 종료 대기                 | 정상 종료 대기                       |
    | **2차 종료 (Hard)** | `taskkill /PID <pid> /F` | `SIGKILL`                      |
    | **특징**           | Explorer 하위 앱은 대부분 정상 종료 | 데몬/백그라운드 프로세스는 Hard Kill 필요 가능 |

---
<br>

## [2-3단계] 환경 변수 관리 (.env)
- DB 접속 정보나 비밀 키 같은 민감한 정보를 코드에 직접 쓰지 않고 외부 파일로 관리
1. `.env` 파일 생성
    ```
    # MongoDB 설정
    MONGO_URL=mongodb://localhost:27017/
    DB_NAME=process_monitor
    COLLECTION_NAME=known_processes

    # 앱 설정
    DEBUG=True
    HOST=0.0.0.0
    PORT=8000
    ```

2. 패키지 설치
    ```
    pip install python-dotenv
    ```
3. 코드 적용 
    ```
    import os
    from dotenv import load_dotenv
    from pymongo import MongoClient

    # .env 파일 로드
    load_dotenv()

    MONGO_URL = os.getenv("MONGO_URL")
    DB_NAME = os.getenv("DB_NAME")

    client = MongoClient(MONGO_URL)
    ```
---
<br>

## [3단계] Git으로 코드 정리 (Windows)
### 1. Git 저장소 초기화
### 2. .gitignore
```
venv/
__pycache__/
*.pyc
.env
```
- venv는 절대 Git에 올리지 않는다 (Linux에서 다시 만들어야 하기 때문)

### 3. 원격 저장소에 push
   
---
<br>

## [4단계] Rocky Linux 서버에서 준비

### 1. Rocky Linux 접속
```
ssh user@서버IP
```

### 2. 필수 패키지 확인
```
python3 --version
git --version

# 없으면
sudo dnf install -y python3 git
```

### 3. 프로젝트 받을 위치
```
mkdir -p ~/projects
cd ~/projects
git clone <레포주소>
cd server-monitor
```

---
<br>

## [5단계] Rocky Linux에서 가상환경 다시 생성

### ⚠️ Windows venv는 사용 불가 → Linux에서 새로 생성

```
python3 -m venv venv
source venv/bin/activate

# 확인:
(venv) [user@rocky server-monitor]$

# 패키지 설치 (Linux)
pip install -r requirements.txt
```

---
<br>

## [6단계] Rocky Linux에서 서버 실행
### 1. FastAPI 서버 실행
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 0.0.0.0 → 외부 접속 허용
- 8000 → 테스트 포트

### 2. 방화벽 확인 (Rocky Linux 필수)
```
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```
- --permanent : 재부팅 후에도 유지
- reload : 설정 즉시 반영

### 3. 외부 접속 확인 (웹 브라우저)

```
http://서버IP:8000/
```
- 모니터링 화면이 나오면 Linux 환경에서 서버 실행 성공

### 4. Nginx 연동 (추후 단계)
> 운영 환경에서는 FastAPI를 직접 노출하지 않는다.

```
Client → Nginx (80) → FastAPI (8000)
```
- FastAPI : 내부 포트 8000
- Nginx : 외부 포트 80
  - Nginx는 Reverse Proxy 역할
  - HTTPS, 인증, 접근 제어는 Nginx에서 처리

#### 👉 Nginx 설정은 운영 단계에서 별도 문서로 진행
---