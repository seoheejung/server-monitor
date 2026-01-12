# server-monitor web

**Rocky Linux 서버의 상태를 웹으로 확인하기 위한 서버 모니터링 프로젝트**

> 이 문서는 server-monitor 프로젝트의 **개발 및 실습 가이드**입니다.


### 프로젝트 목표
* 서버의 CPU, 메모리, 디스크 상태를 어떻게 프로그램으로 확인할 수 있을까?
* Linux에서 실행 중인 서비스(nginx, docker 등)의 상태를 어떻게 코드로 알 수 있을까?
* 이런 정보를 웹 화면으로 보여주려면 어떤 도구가 필요할까?

---

<br>

## FastAPI 선택 이유

### 1. FastAPI란?
> FastAPI : **Python으로 웹 서버(API 서버)를 쉽게 만들 수 있게 도와주는 도구**
> Python 코드로 웹 주소(URL)에 접속했을 때 어떤 동작을 할지 정의할 수 있는 프레임워크


* `/cpu` 라는 주소로 접속하면 → CPU 사용률을 보여준다
* `/dashboard` 로 접속하면 → 웹 화면(HTML)을 보여준다

<br>

### 2. 왜 그냥 Python 파일로는 안 되는가?

```bash
python test.py
```

하지만 이렇게 실행한 프로그램은:
* 웹 브라우저에서 접속 불가
* 여러 사용자의 요청을 동시에 처리하기 힘듦
* 서버 프로그램처럼 계속 켜두기 불편함

👉 **서버 상태를 웹으로 보여주려면 "웹 서버"가 필요**

<br>

### 3. FastAPI를 선택한 이유

* Python 문법 그대로 사용 (기초 문법만 알아도 가능)
* 코드가 짧고 읽기 쉬움
* 서버 상태 확인 같은 가벼운 작업에 적합
* 나중에 기능을 하나씩 추가하기 쉬움

👉 즉, **리눅스 서버 모니터링 실습용으로 가장 부담이 적은 선택**

---

<br>

## FastAPI가 이 프로젝트에서 하는 역할

#### FastAPI는 이 프로젝트에서 **중간 관리자** 역할

```
[ Rocky Linux 서버 ]
        |
        |  (CPU, 메모리, 로그 읽기)
        v
[ Python 코드 ]
        |
        |  FastAPI
        v
[ 웹 브라우저 ]
```

* Linux에서 정보를 읽는다
* FastAPI가 그 정보를 웹 요청에 맞게 전달한다
* 브라우저에서 결과를 확인한다

---

<br>

## 프로젝트 디렉토리 구조 설명

```
web/
├── app/
│   ├── main.py          # FastAPI 서버 시작 지점
│   ├── system/          # 서버 정보 수집 코드 모음
│   │   ├── cpu.py       # CPU 사용량
│   │   ├── memory.py    # 메모리 사용량
│   │   ├── disk.py      # 디스크 사용량
│   │   ├── uptime.py    # 서버 업타임
│   │   ├── service.py   # 서비스 상태 (systemctl)
│   │   ├── log.py       # 로그 tail 기능
│   │   └── process.py   # (확장) 프로세스 분석
│   ├── templates/       # 웹 화면(HTML)
│   │   └── dashboard.html
│   └── static/          # 정적 파일
│       └── style.css
├── db/
│   └── monitor.db       # (추후 사용) 데이터 저장용 DB
├── requirements.txt     # 설치해야 할 패키지 목록
└── README.md
```

### main.py는 왜 중요한가?

`main.py`는 **FastAPI 서버가 시작되는 파일 (FastAPI 엔트리)**

* 이 파일이 실행되면 웹 서버가 켜짐
* 모든 URL과 기능이 여기서 연결됨

---

<br>

## 왜 가상환경(venv)을 사용하는가?

이 프로젝트는 **서버에서 실행되는 프로그램**이기 때문에, Python 환경을 깨끗하게 관리하는 것이 중요

가상환경을 사용하는 이유:

* 이 프로젝트 전용 Python 환경을 만들기 위해
* 서버 전체 Python에 영향을 주지 않기 위해
* 나중에 프로젝트를 옮겨도 같은 환경을 재현하기 위해

> 서버에서 Python 프로젝트를 안전하게 관리하기 위해 사용하는 기본 습관

```bash
python3 -m venv venv
source venv/bin/activate
```

* `server-monitor` 전용 Python 공간 생성
* FastAPI, psutil 등을 안전하게 설치 가능

---

<br>

## 프로젝트 진행 흐름
1. Windows에서 먼저 FastApi 실행 확인
2. Linux(Rocky) 서버에 git pull
3. 서버 환경에서 다시 실행

### 1단계: Windows에서 FastAPI 서버 실행 확인
1. 가상환경 생성
    ```
    python -m venv venv
    ```
2. 보안 설정
   - Windows PowerShell은 보안 때문에
   - 기본적으로 .ps1 스크립트 실행을 막아둠
   - Activate.ps1는 PowerShell 스크립트 그래서 가상환경 활성화가 차단됨
   - powerShell을 관리자 말고 그냥 그대로 열고:
    ```
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    ```
    | 항목           | 설명             |
    | ------------ | -------------- |
    | CurrentUser  | 내 계정에만 적용      |
    | RemoteSigned | 인터넷에서 받은 것만 제한 |
    | 로컬 venv 스크립트 | 실행 가능          |

3. 가상환경 활성화 (Windows PowerShell)
    ```
    venv\Scripts\activate
    ```
   - 프롬프트에 (venv) 뜨면 OK

4. 패키지 설치 (Windows)
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

5. app/main.py 작성
    ```
    from fastapi import FastAPI

    app = FastAPI(title="server-monitor")

    @app.get("/")
    def root():
        return {"message": "server-monitor running"}
    ```

6. FastAPI 서버 실행 (Windows)
    ```
    uvicorn app.main:app --reload

    # 성공하면 콘솔에 입력
    Uvicorn running on http://127.0.0.1:8000
    ```

7. 브라우저 확인 (http://127.0.0.1:8000/)
    ```
    {"message":"server-monitor running"}
    ```

<br>

#### * FastAPI 서버를 실행할 때마다 가상환경(venv)을 켜야한다.
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

👉 venv 매번 켬

2. 나중 (Rocky Linux 운영)
- systemd / supervisor / docker
- 실행 스크립트에 venv 경로를 명시
- 운영자가 직접 activate 안 함

```
/opt/server-monitor/venv/bin/uvicorn app.main:app
```
👉 운영에서는 자동

<br>

### 2단계: 시스템 정보 API 구현
1. CPU 정보 API부터 만들기
   - psutil 중 가장 단순
   - OS 권한 문제 없음
   - Windows / Linux 동일 코드
    ```
    import psutil

    def get_cpu_usage():
        return {
            "cpu_percent": psutil.cpu_percent(interval=1)
        }
    ```
2. 메모리 → 디스크 → 구동 시간 순으로 진행
    - 메모리: psutil.virtual_memory()
    - 디스크: psutil.disk_usage('/')
    - 구동 시간: psutil.boot_time() 또는 /proc/uptime
3. 서비스 상태 / 로그 수집
    - 운영체제에 따른 분기 처리 필요
    - 서비스 상태
        - Linux: systemctl is-active
            ```
            systemctl is-active nginx
            systemctl is-active docker
            ```
            - Python에서 subprocess로 실행
            - systemctl 실행 시 권한 문제를 고려하여 sudo 설정 또는 실행 사용자 분리
            - 결과: active / inactive / failed
        - Windows: 미지원 (예외 처리)
    - 로그 tail
        - Linux 로그 파일 직접 읽기
            ```
            /var/log/nginx/access.log
            /var/log/messages
            ```
        - 최근 N줄만 읽기
        - 파일 직접 읽기 (tail 구현)
        - 로그 파일 접근 시 권한 제한 및 민감 정보 노출 방지 고려

4. 대시보드
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

        ```
        - Retro / Pixel Server Console
        - 도트 배경 → 서버 콘솔 느낌
        - 픽셀 폰트 → 시스템 모니터링 감성
        - 굵은 테두리 → 상태판 느낌
        - box-shadow → 픽셀 카드 연출
    - 핵심 포인트
    - service 상태는 문자열(active, inactive)
    - 로그는 리스트
    - CPU/메모리는 CSS class 계산해서 넘김

<br>

### ✨ 추가 기능 : 프로세스 분석 & 보안 관점 모니터링

> 단순히 CPU/메모리 수치만 보여주는 모니터링이 아니라,   
> “현재 서버에서 무엇이 돌아가고 있고, 이게 위험한지 아닌지”를 설명하는 것을 추가  
> 정보 수집, 위험 판단, 사람이 이해 가능한 설명, 시각적 상태 표현 등으로    
> “서버가 왜 위험한지 설명해주는 모니터링” 구현   

### 🔍 실행 중인 프로세스 분석 기능 (Cross Platform)
#### 1. 수집 정보
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
├── collect_processes()        # OS 공통 (psutil)
├── collect_ports(pid)         # OS별 분기
├── analyze_process(proc)      # 경고 판단
├── explain_process(proc)      # 프로세스 의미 설명
└── get_process_list()         # 최종 조합 함수
```

#### 💡 Rocky Linux(Linux) 이식 시 주의사항 업데이트
1. username: Windows의 SYSTEM, Administrator 대신 Linux의 root가 주 감시 대상 (이미 코드에 포함)
2. standard_paths: Linux 특유의 경로인 /var/lib, /tmp 등이 SUSPICIOUS_PATH 판단 기준에 추가 가능
3. 포트 수집 권한: Linux에서는 sudo 권한 없이 실행할 경우 다른 사용자의 프로세스 포트(collect_ports)를 읽어오지 못할 수 있으므로 실행 권한 검토 필요
   
<br> 

#### 2. 위험 요소(Warning) 자동 분석
- 각 프로세스에 대해 보안/운영 관점 경고 자동 판단
- “정상 동작”과 “주의 필요”를 사람이 바로 이해 가능

| 경고                | 의미                 | 판단 기준        | 
| ----------------- | ------------------ |------------------ |
| RUNNING_AS_ROOT   | root/관리자 권한으로 실행 중 | username이 root, SYSTEM, Administrator인 경우 |
| PUBLIC_PORT(n)    | 위험/주요 포트 외부 노출 | KNOWN_PORTS에 정의된 포트 점유 시 설명 포함 |
| SYSTEM_PORT(n)    | 비표준 시스템 포트 개방 | 1024 미만 포트 중 정의되지 않은 포트 사용 시 |
| HIGH_MEMORY_USAGE | 메모리 사용량 과다     | memory_percent가 20% 이상일 때 |
| SUSPICIOUS_PATH   | 비정상 경로에서 실행    | 표준 경로(bin, Program Files 등)가 아닐 때 |

#### 보안 진단 가이드 로직
1. KNOWN_PROCESSES에 명칭이 있고 warnings가 없으면? [안전]
2. KNOWN_PROCESSES에 명칭이 없는데 warnings가 없으면? [경계] (사용자 확인 필요)
3. warnings가 하나라도 있으면? [위험/주의] (즉시 조치 권고)

```
CASE A: 정체는 알지만 위험은 없는 경우
- 프로세스: explorer.exe (윈도우 탐색기)
- Explain: KNOWN_PROCESSES에 있음 → "Windows 탐색기: 파일 관리 및 데스크톱 UI"
- Warnings: 권한/경로/포트 모두 정상 → "✅ 특이사항 없음"
- 결과: 사용자 안심. "아, 탐색기가 정상적으로 잘 돌아가고 있구나."

CASE B: 정체는 모르지만 위험은 없는 경우
- 프로세스: my_custom_tool.exe (내가 직접 만든 도구)
- Explain: KNOWN_PROCESSES에 없음 → "❓ 알 수 없는 사용자/시스템 프로세스"
- Warnings: 권한/경로/포트 모두 정상 → "✅ 특이사항 없음"
- 결과: 보통 수준의 경계. "용도는 모르겠지만 딱히 위험한 짓을 하고 있지는 않네."

CASE C: 정체도 모르고 위험도 있는 경우 (가장 위험)
- 프로세스: hacker_tool.exe
- Explain: KNOWN_PROCESSES에 없음 → "❓ 알 수 없는 사용자/시스템 프로세스"
- Warnings: 관리자 권한, 비표준 경로 등 발견 → "⚠️ SUSPICIOUS_PATH"
- 결과: 즉각 조치 필요. "뭔지도 모르는 게 위험한 권한으로 이상한 곳에서 실행 중이네!"
```

<br>

#### 3. 프로세스 설명(Explain) 및 보안 가이드
- 프로세스의 원형(Generic Name)을 기반으로 한글 역할 설명 제공
- 위험 요소(Warnings)와 결합하여 "현재 상태"를 직관적으로 표현

```
- nginx (웹 서버)
  └ 역할: 외부 HTTP 요청 처리 및 로드 밸런싱
  └ 상태: ⚠️ PUBLIC_PORT:80 (비암호화 포트 노출)

- redis (데이터 저장소)
  └ 역할: 고속 캐시 및 세션 저장소
  └ 상태: ⚠️ PUBLIC_PORT:6379 (DB 포트 외부 노출 위험)
```

| 프로세스(이름) | 설명(Explain) | 탐지된 위험(Warnings) | 
| ----------------- | ------------------ |------------------ |
| nginx | 웹 서버: 외부 요청을 처리하고 파일/앱을 연결 | ⚠️ PUBLIC_PORT(80): 보안 연결 권장 | 
| redis-server | 인메모리 저장소: 고속 캐시 및 세션 관리용 | ⚠️ PUBLIC_PORT(6379): 외부 접근 주의 | 
| lsass.exe | Windows 보안: 사용자 로그인 및 권한 관리 | ✅ 특이사항 없음 | 

<br>

#### 4. 도트 기반 콘솔 UI (Retro Server Dashboard)
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

<br>

### 3단계: Git으로 코드 정리 (Windows)
1. Git 저장소 초기화
2. .gitignore
    ```
    .gitignore 파일 생성
    venv/
    __pycache__/
    *.pyc
    .env
    ```

    👉 venv는 절대 Git에 올리지 않는다 (Linux에서 다시 만들 거기 때문)

3. 원격 저장소에 push
   
<br>

### 4단계: Rocky Linux 서버에서 준비

1. Rocky Linux 접속
    ```
    ssh user@서버IP
    ```

2. 필수 패키지 확인
    ```
    python3 --version
    git --version

    # 없으면
    sudo dnf install -y python3 git
    ```

3. 프로젝트 받을 위치
    ```
    mkdir -p ~/projects
    cd ~/projects
    git clone <레포주소>
    cd server-monitor
    ```

<br>

## 5단계: Rocky Linux에서 가상환경 다시 생성

### ⚠️ Windows venv는 사용 불가 → Linux에서 새로 생성

```
python3 -m venv venv
source venv/bin/activate

# 확인:
(venv) [user@rocky server-monitor]$

# 패키지 설치 (Linux)
pip install -r requirements.txt
```

<br>

##  6단계: Rocky Linux에서 서버 실행
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 0.0.0.0 → 외부 접속 허용
- 8000 → 테스트 포트

### 방화벽 확인 (Rocky Linux 필수)
```
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### 외부 접속 확인

#### 브라우저에서: http://서버IP:8000/
👉 JSON 나오면 Linux 단계도 성공

### Nginx 연동
- FastAPI → 8000
- Nginx → 80
- Reverse Proxy 설정
  
---

