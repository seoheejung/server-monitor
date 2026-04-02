# 서버 모니터링 웹 애플리케이션 - Server Monitoring & Process Security Engine

**서버의 상태를 웹으로 확인하기 위한 서버 모니터링 프로젝트**

> 본 문서는 웹 애플리케이션 구조와 내부 설계를 설명한다.   
> 개발 환경 구축 단계는 기록 목적이며, 운영 기준은 아니다.

---
<br>

## 📑 목차

- [[설계] 핵심 기능](#설계-핵심-기능)
- [프로젝트 구조](#프로젝트-구조)
- [[1단계] Windows에서 FastAPI 서버 실행 확인](#1단계-windows에서-fastapi-서버-실행-확인)
- [[2단계] API 구현](#2단계-api-구현)
- [[3단계] 프로세스 분석 & 보안 관점 모니터링](#3단계-프로세스-분석--보안-관점-모니터링)
- [[4단계] 운영 정책 저장소 (MongoDB) & 프로세스 제어](#4단계-운영-정책-저장소-mongodb--프로세스-제어)
- [[5단계] 환경 변수 관리 (.env)](#5단계-환경-변수-관리-env)
- [이 문서의 범위](#이-문서의-범위)

---
<br>


### 문서 라벨 기준

- 🧭 [설계] : 왜 이렇게 설계했는가 (판단 기준·구조)
- 🧪 [구현] : 어떻게 만들었는가 (코드·구조)
- ▶ [실행] : 어떻게 실행하는가 (환경·명령)

---
<br>

##  🧭 [설계] 핵심 기능
### 1. 기본 모니터링 (1차)
- 시스템 리소스 시각화
  - CPU, RAM, Disk 사용량을 픽셀 스타일 대시보드로 실시간 확인
- 하이브리드 서비스 모니터링
  - Linux: systemctl 기반 서비스 상태 감지
  - Docker / Native: psutil 기반 프로세스 상태 분석
  - 로그 스트리밍: 시스템 및 서비스 로그를 웹 콘솔에서 즉시 확인
### 2. 프로세스 보안 분석 (2차)
- 실행 중 프로세스 상세 분석 (Cross Platform)
  - root/SYSTEM 실행 여부, 비표준 경로, 위험·시스템 포트 점유 자동 진단
- Explain & Warning
  - 각 프로세스의 역할과 현재 위험 요소를 사용자가 이해 가능한 언어로 설명
  - 정상 / 주의 / 위험 상태를 도트 기반 콘솔 UI로 시각화
### 3. 운영 제어 & 정책 관리 (3차)
- 정책 기반 프로세스 관리
  - MongoDB 연동으로 KNOWN_PROCESSES 및 보호 정책 중앙 관리
- 안전한 프로세스 종료
  - 시스템 프로세스 보호
  - Soft Kill → Hard Kill 단계적 종료 로직
- 운영 확장 기반
  - 운영자 개입 없이 정책에 따른 판단·제어 구조 확보

---
<br>

## 🧪 프로젝트 구조

```
web/
├── app/
│   ├── main.py          # FastAPI 엔트리 (URL 및 서버 설정)
│   ├── core/            # 전역 설정
│   │   ├── config.py
│   │   ├── response.py  # 공통 응답 래퍼
│   │   └── security.py  # 보안 설정
│   ├── routes/          # URL
│   │   ├── auth.py           # 인증 관련 API
│   │   ├── admin.py          # 관리자 API (sync-now 등)
│   │   ├── process.py        # 프로세스 관련 API
│   │   └── dashboard.py      # 대시보드 관련 API
│   ├── repositories/
│   │   └── db.py
│   ├── constants/       # 포트 / 프로세스 정책
│   │   ├── ports.py
│   │   ├── linux.py
│   │   └── windows.py
│   ├── services/
│   │   ├── init/       
│   │   │   └── process_seed.py  #  초기 데이터 로드/검증/시드 준비
│   │   ├── system/          # 서버 상태 모음
│   │   │   ├── cpu.py       # CPU 사용량
│   │   │   ├── memory.py    # 메모리 사용량
│   │   │   ├── disk.py      # 디스크 사용량
│   │   │   ├── uptime.py    # 서버 업타임
│   │   │   ├── service.py   # 서비스 상태 (systemctl)
│   │   │   ├── log.py       # 로그 tail 기능
│   │   │   ├── process_control.py    # 프로세스 종료 로직
│   │   │   └── process_analyzer.py   # 프로세스 분석
│   ├── utils/
│   │   └── env.py       # 컨테이너 / 런타임
│   ├── templates/       # 웹 화면
│   │   └── dashboard.html
│   └── static/          # 정적 파일
│       ├── dashboard.js
│       └── style.css
├── data/
├── .env                 
├── .gitignore           
├── requirements.txt     # 의존성 패키지 목록
├── run.py               # 서버 통합 실행 스크립트
└── README.md
```

### 프로젝트 진행 흐름

> 🗂️ Windows 개발  → Linux 이식  → 운영 환경 확장

#### Linux 이식 및 검증 전략 (Docker → VirtualBox)

- Linux 이식은 **Docker 기반 Rocky Linux 컨테이너**에서 먼저 진행
  - Git pull 후 즉시 실행 가능
  - psutil, /proc, 포트 수집 등 **OS 의존 로직 빠른 검증**
  - systemd 미지원 환경에서의 fallback 로직 확인

- 이후 **VirtualBox 기반 Rocky Linux 네이티브 환경**에서 최종 검증
  - systemctl, firewalld, 권한 모델 포함
  - 실제 운영 서버와 동일한 조건에서 동작 여부 확인

---
<br>

## ▶ [1단계] Windows에서 FastAPI 서버 실행 확인
### 1. 가상환경 생성
```
python -m venv venv
```

### 2. 가상환경 활성화 (Windows PowerShell)
```
venv\Scripts\activate
```
- 프롬프트에 (venv) 뜨면 OK

### 3. 패키지 설치 (Windows)
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

### 4. FastAPI 서버 실행 (Windows)
```
uvicorn app.main:app --reload

# 성공하면 콘솔에 입력
Uvicorn running on http://127.0.0.1:8000
```

### 5. 브라우저 확인 (http://127.0.0.1:8000/)
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
   - 👉 운영 환경에서는 자동

---
<br>

## 🧪 [2단계] API 구현

### 1. 시스템 정보 수집 (CPU)
- psutil 중 가장 단순 (OS 권한 문제 없음)
- API 응답 지연 방지를 위해 blocking 방식(interval>0)은 사용하지 않음
- psutil.cpu_percent(interval=None) 기반 즉시 반환값 사용
- Windows와 Linux에서 동일한 API로 동작하여 개발 편의성 확보

### 2. 리소스 가공 (메모리, 디스크, 구동 시간)
#### 메모리: psutil.virtual_memory()
- 전체(Total), 사용량(Used), 퍼센트(Percent) 추출

#### 디스크: psutil.disk_usage('/')
- OS별 루트 경로 분기 처리
  1. Linux : `/`
  2. Windows : `C:\\`

#### 구동 시간: psutil.boot_time()
- 부팅 시점 타임스탬프와 datetime.now()의 차이를 계산
- timedelta를 사용하여 D+H:M 형태의 사용자 친화적 문자열로 가공

### 3. 서비스 상태
#### 운영체제에 따른 분기 처리 필요
1. Windows: `platform` 체크를 통해 미지원 메시지 출력 및 예외 처리
2. Linux (Host): `systemctl is-active` 명령어를 우선 사용하여 OS 레벨의 표준 상태 수집
3. Docker (Container): `systemctl`이 없는 환경은 `psutil.process_iter`로 프로세스명 검색

#### 모니터링 대상 서비스 정의 (services_to_check)
1. 네트워크/인프라: nginx (웹 서비스), sshd (원격 관리)
2. 시스템 운영: rsyslog (로그 관리), docker (가상화 서비스)
3. 실행 환경: python (백엔드 구동 환경)

### 4. 로그 수집 (tail)
- 대용량 로그 파일 전체를 읽지 않고, 파일 끝(EOF)에서부터 최근 10~20줄만 추출하는 tail 로직 구현
- `/var/log` 접근 시 발생할 수 있는 **PermissionError**를 `try-except`로 처리하여 서버가 중단되지 않게 방어 코드 작성

### 5. 대시보드
#### Jinja2 템플릿을 활용한 화면 분리
```
Python 데이터 → Jinja2 → HTML
```
#### UI 컨셉
1. Retro / Pixel Server Console
2. 도트 배경 → 서버 콘솔 느낌
3. 픽셀 폰트 → 시스템 모니터링 감성
4. 굵은 테두리 → 상태판 느낌
5. box-shadow → 픽셀 카드 연출
6. 리소스 수치에 따라 good/warn/bad CSS 클래스 자동 부여
7. 서비스 상태(active, failed)에 따라 도트 색상 변경

### 6. 관리자 인증 구조
- 모든 주요 API는 인증이 필요

#### 인증 방식
1. 로그인 요청
    - 클라이언트는 /api/auth/login에 username, password를 전달
    - 서버는 환경변수 ADMIN_USERNAME, ADMIN_PASSWORD와 비교하여 검증
2. 세션 발급
    - 인증 성공 시 서버는 admin_session 쿠키를 발급 (HttpOnly)
    - 쿠키 값은 랜덤 세션 토큰이며, 서버 메모리에 저장된 세션과 매칭됨

#### 이후 요청
- `/api/dashboard`
- `/api/process/terminate`
- `/api/admin/*`

모든 API는 세션 쿠키(`admin_session`) 검증을 통해 접근 제어

#### 특징
- 아이디/비밀번호는 로그인 시 1회만 사용
- 이후 요청은 세션 쿠키 기반 인증 유지
- 쿠키에는 인증 정보가 아닌 랜덤 세션 토큰만 저장
- 세션은 서버 메모리에서 관리되며, 만료 시간 이후 자동 무효화됨 (4시간)
---
<br>

## 🧭 [3단계] 프로세스 분석 & 보안 관점 모니터링

> ⚠️ 프로세스 분석의 상세 판단 기준과 예외 정책은 `docs/POLICY.md` 문서 참조

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
1. KNOWN_PROCESSES에 존재 + Warning 없음 → ✅ 안전 (단, 경로/권한/포트가 정상 범위인 경우에 한함)
2. KNOWN_PROCESSES에 없음 + Warning 없음 → ⚠️ 경계 (사용자 확인 필요)
3. Warning이 하나라도 존재 → 🚨 위험 / 주의 (즉시 점검 권장)
   - 일반 Warning → ⚠️ 주의
   - 치명 Warning(비정상 경로, 권한 이상 등) → 🚨 위험 (즉시 점검 권장)
```
CASE A: 정체는 알고 있고, 위험도 없는 경우
- Process: explorer.exe (윈도우 탐색기)
- Explain: KNOWN_PROCESSES에 있음 → "Windows 탐색기: 파일 관리 및 데스크톱 UI"
- Warnings: 권한/경로/포트 모두 정상 → "✅ 특이사항 없음"
- 결과: ✅ 정상 동작 (정상 경로 및 권한 기준 충족)

CASE B: 정체는 모르지만, 위험도 없는 경우
- Process: my_custom_tool.exe (내가 직접 만든 도구)
- Explain: KNOWN_PROCESSES에 없음 → "❓ 알 수 없는 사용자/시스템 프로세스"
- Warnings: 권한/경로/포트 모두 정상 → "✅ 특이사항 없음"
- 결과: ⚠️ 경계 (용도만 확인하면 됨)

CASE C: 정체도 모르고, 위험도 있는 경우 (최우선 대응)
- Process: hacker_tool.exe
- Explain: KNOWN_PROCESSES에 없음 → "❓ 알 수 없는 사용자/시스템 프로세스"
- Warnings: 관리자 권한, 비표준 경로 등 발견 → "⚠️ SUSPICIOUS_PATH"
- 결과: 🚨 즉시 조치 필요 (치명 Warning 포함)
```

<br>

### 4. 도트 기반 콘솔 UI (Retro Server Dashboard)
- 상태 표현 규칙
  
| 상태 | 도트 |
| -- | -- |
| 정상 | 🟢 |
| 주의 | 🟡 |
| 위험 | 🔴 |

---
<br>

## 🧭 [4단계] 운영 환경 정책 저장소 (MongoDB) & 프로세스 제어

### 1. MongoDB
### MongoDB 인증 구조

본 시스템은 MongoDB 인증이 활성화된 상태로 운영된다.

- 관리자 계정과 애플리케이션 계정을 분리하여 사용한다.
- 애플리케이션은 관리자 계정이 아닌 전용 DB 계정으로만 접근한다.
- 애플리케이션 계정은 `process_monitor` 데이터베이스에 한정된 권한을 가진다.

#### MongoDB 인증 관련 주의사항

- MongoDB 관리자 계정 및 애플리케이션 계정 생성 후 `.env`에 반영해야 한다.
- 인증이 활성화된 상태이므로, 계정 정보 없이 DB에 접근할 수 없다.
- `mongodb://localhost:27017/` 형태의 무인증 접속은 운영 환경에서 지원하지 않는다.

#### 접속 방식
```
mongodb://<app_user>:<app_password>@localhost:27017/process_monitor?authSource=process_monitor
```
- `authSource=process_monitor`: 인증을 수행할 데이터베이스 지정

#### 로컬 테스트 (Docker)

```bash
# 기존 컨테이너/데이터 제거 (초기화 보장)
docker rm -f mongo-local 2>/dev/null || true
docker volume rm mongo-local-data 2>/dev/null || true

# MongoDB 컨테이너 실행
docker pull mongo:7

docker run -d \
  --name mongo-local \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin_password \
  mongo:7

# 애플리케이션 계정 생성
docker exec -it mongo-local mongosh \
  -u admin \
  -p admin_password \
  --authenticationDatabase admin \
  --eval 'db = db.getSiblingDB("process_monitor"); db.createUser({ user: "app_user", pwd: "app_password", roles: [ { role: "readWrite", db: "process_monitor" } ] })'

# 접속 확인
docker exec -it mongo-local mongosh \
  "mongodb://app_user:app_password@localhost:27017/process_monitor?authSource=process_monitor" \
  --eval 'db.runCommand({ ping: 1 })'
```
- 로컬에서는 MongoDB 계정을 수동으로 생성해야 하며, 기존 데이터가 남아 있으면 초기화 후 재실행해야 한다.

#### 설계 (KNOWN_PROCESSES 전용)
- KNOWN_PROCESSES = 판단 기준 사전
- 실행 중 프로세스 저장 ❌
- KNOWN_PROCESSES에 정의된 프로세스만 활용
- 매칭 실패 시 → Unknown Process 로 처리 (DB 저장 ❌)

> MongoDB는 정책 저장소 역할만 수행하며,   
> 모든 최종 판단은 실시간 프로세스 정보(psutil)를 기준으로 한다.

<br>

#### `known_processes` 컬렉션 구조
```json
{
    "_id": ObjectId,

    "name": "svchost.exe",
    "platform": "windows",
    "category": "system_core",
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

| **필드명** | **데이터 타입** | **설명** | **비고** |
| --- | --- | --- | --- |
| **`name`** | String | 프로세스 실행 파일명 | **반드시 소문자 저장** (Case-insensitive 매칭) |
| **`platform`** | String | 운영체제 구분 | `windows`, `linux`, `common` 중 택 1 |
| **`category`** | String | 기능적 분류 | 설계된 10개 카테고리 중 매핑 |
| **`description`** | String | 프로세스 역할 기술 | UI 표시 및 `is_system` 판별 근거 |
| **`policy`** | Object | 관리 정책 서브 도큐먼트 |  |
| └ `is_system` | Boolean | 시스템 핵심 여부 | `true` 시 종료 보호 로직 활성화 |
| └ `terminatable` | Boolean | 강제 종료 가능 여부 | `is_system` 값에 종속됨 |
| └ `reason` | String | 정책 결정 사유 | "System Core" 또는 "User Application" |
| **`tags`** | Array | 분류/검색용 태그 | `[platform, "auto-imported"]` 기본 구성 |
| **`created_at`** | Date | 정책 생성 시각 | ISO 8601 형식 |

#### 인덱스 설계
```js
db.known_processes.createIndex(
    { name: 1, platform: 1 },
    { unique: true }
)
```
- 복합 인덱스 생성 (name: 1, platform: 1)
- unique=True로 설정하여 중복 데이터 방지

#### 데이터 변환 및 분류 규칙
1. Platform 판별
    - Windows: 파일명이 .exe로 끝나거나, 설명(desc) 내에 "Windows" 단어가 포함된 경우
    - Common: 플랫폼에 관계없이 동일한 이름을 사용하는 오픈소스/범용 소프트웨어 (docker, nginx, node, python, mysql 등)
    - Linux: 위 두 조건에 해당하지 않는 모든 케이스

2. System 여부 및 Policy 확정 (Hard-coded Logic)
    - 판단의 모호함을 제거하기 위해 is_system 값에 따라 정책을 강제 동기화한다.
    - `is_system true` 조건: 설명(desc) 필드에 ["시스템", "커널", "core", "보안", "관리자", "driver", "infrastructure"] 중 하나라도 포함될 경우.
        - 결과: policy.terminatable = false, policy.reason = "System Core"
    - `is_system false` 조건: 위 키워드가 포함되지 않은 모든 경우.
        - 결과: policy.terminatable = true, policy.reason = "User Application"

3. Category 매핑 가이드 (Strict Mapping)
    - kernel / core: 부팅 및 OS 유지 필수 (예: init, ntoskrnl.exe)
    - database: DB 엔진 (예: mysqld, postgres)
    - network-service: 네트워크 연결, 원격 접속 및 시간 동기화 관리 (예: sshd, networkmanager)
    - system-service: 백그라운드에서 시스템 기능 보조 및 로그/권한 관리 (예: svchost.exe, polkitd)
    - monitoring: 시스템 리소스 상태 감시 및 프로세스 활동 추적 (예: top, htop)
    - container-runtime: 컨테이너의 격리 실행 및 생명주기 관리 레이어 (예: containerd, tini)
    - web-server: 웹 요청 처리 및 라우팅 (예: nginx, apache)
    - runtime: 프로그래밍 언어 실행 환경 (예: java, python, node)
    - infrastructure: 가상화 및 클러스터 관리 (예: docker, kubelet)
    - system-utility: CLI 도구 및 단순 명령 (예: grep, powershell.exe)

4. 기타 필드
    - 기본적으로 "general"로 설정
    - tags는 [platform, "auto-imported"] 구성
    - created_at 필드 추가 (ISO 8601 형식)

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
    | 구분        | Windows                 | Linux               |
    | --------- | -------------------------- | ----------------------- |
    | **종료 대상** | explorer.exe 하위 프로세스  | 로그인 사용자 UID 소유   |
    |           | 사용자 계정 소유            | TTY / graphical session |
    |           | GUI 세션에 속함          | `/home/*` 경로 실행 파일      |
    |           | UWP / Win32 사용자 앱      |                         |
    | **제외 대상** | SESSION 0             | UID 0 (root)            |
    |           | SYSTEM / LOCAL SERVICE     | systemd / daemon        |
    |           | Windows signed core binary | `/usr/lib/systemd`      |
    |           | svchost 계열           |                         |

<br>

2. 프로세스 종료 판단 플로우
    ```
    [프로세스 수집]
        ↓
    [KNOWN_PROCESSES Mongo 조회]
        ↓
    [process_rules 조회]   (있다면)
        ↓
    [policy.is_system 확인 (MongoDB)]
        ↓
    [policy.terminatable 확인 (MongoDB)]
        ↓
    [psutil 기반 시스템 보호 재확인]
    ```
    - PID / UID / SESSION 판단은 실시간 데이터
    - 이름 기준 정책만 `MongoDB`
    - process_rules는 향후 자동 종료 정책 확장 시 도입 예정

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
    | 단계         | Windows       | Linux                |
    | ---------------- | ------------------------ | ------------------- |
    | **1차 종료 (Soft)** | `taskkill /PID <pid>` | `SIGTERM`     |
    | **대기**           | 정상 종료 대기      | 정상 종료 대기   |
    | **2차 종료 (Hard)** | `taskkill /PID <pid> /F` | `SIGKILL`   |
    | **특징**   | Explorer 하위 앱은 대부분 정상 종료 | 데몬/백그라운드 프로세스는 Hard Kill 필요 가능 |

---
<br>

## 🧪 [5단계] 환경 변수 관리 (.env)

> DB 접속 정보나 비밀 키 같은 민감한 정보를 코드에 직접 쓰지 않고 외부 파일로 관리

### 1. `.env` 파일 생성
```
# MongoDB 설정 (인증 필수)
MONGO_URL=mongodb://app_user:app_password@localhost:27017/process_monitor?authSource=process_monitor
DB_NAME=process_monitor
COLLECTION_NAME=known_processes

# 앱 설정
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 개발용 데이터 초기화 허용 여부
# True면 시드 적재 전에 컬렉션을 drop 할 수 있음
# 운영 환경에서는 반드시 False 유지
ALLOW_SEED_RESET=False
```

### 2. 패키지 설치
```
pip install python-dotenv
```
### 3. 코드 적용 
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

### 4. 운영 환경과의 차이

- 로컬 환경: `.env` 파일을 직접 생성하여 사용
- 운영 환경: Ansible Vault → 템플릿(`app.env.j2`)을 통해 `.env` 자동 생성
```
vault.yml → Ansible 변수 → app.env.j2 → .env
```

---
<br>

## 이 문서의 범위

- FastAPI 기반 웹 애플리케이션 구조
- API / 템플릿 / 시스템 수집 로직 구성
- 개발 및 실행 흐름 정리

> ※ 설계 의도 및 판단 기준: docs/FASTAPI_DEV.md 참조  
> ※ Linux Native 실행 검증: docs/NATIVE_RUN.md 참조  
> ※ 운영 환경 자동화 기준: docs/ANSIBLE_INFRA.md 참조  
> ※ 프로세스 보안 정책: docs/POLICY.md 참조  
> ※ 인프라 디렉토리 및 자동화 구조 개요: infra/README.md 참조

---
