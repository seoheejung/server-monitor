# server-monitor

**Rocky Linux 서버의 상태를 웹으로 확인하기 위한 서버 모니터링 프로젝트**

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
│   │   └── log.py       # 로그 tail 기능
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
        - Windows: 미지원 (예외 처리)
    - 로그 tail
        - Linux 로그 파일 직접 읽기
        - 접근 권한 및 민감 정보 노출 고려
4. 대시보드
    - Jinja2 템플릿을 활용한 화면 분리
    ```
    Python 데이터 → Jinja2 → HTML
    ```
    - UI 컨셉
        - Retro / Pixel Server Console
        - 도트 배경 → 서버 콘솔 느낌
        - 픽셀 폰트 → 시스템 모니터링 감성
        - 굵은 테두리 → 상태판 느낌
        - box-shadow → 픽셀 카드 연출
    - 핵심 포인트
    - service 상태는 문자열(active, inactive)
    - 로그는 리스트
    - CPU/메모리는 CSS class 계산해서 넘김

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

👉 venv는 절대 Git에 올리지 않는다
(Linux에서 다시 만들 거기 때문)

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