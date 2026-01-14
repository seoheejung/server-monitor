# 서버 관리형 프로젝트 : 서버 상태 모니터링 대시보드
#### 서버에서 실행 중인 리소스, 서비스, 프로세스를 수집하고,<Br> 그 상태와 위험 요소를 사람이 이해할 수 있게 웹으로 시각화하는 서버 모니터링 프로젝트
 
#### 단순 수치 나열이 아니라 “지금 이 서버에서 무엇이 돌고 있고, 이게 안전한지”를 설명하는 대시보드

#### server-monitor는 서버 상태를 ‘수치’가 아니라 ‘의미’로 보여주는 프로젝트

<br>

## 프로젝트 개요

> Rocky Linux 서버의 시스템 리소스(CPU, 메모리, 디스크),
> 서비스 상태(systemctl), 로그, 실행 중인 프로세스를 수집하여
> Retro / Pixel 콘솔 스타일 웹 대시보드로 보여준다.
>
> 서버 상태를 숫자가 아니라 “이해 가능한 정보”로 보여주는 것
>
> 서버를 잘 모르는 사람도 “지금 이 서버가 안전한지” 판단할 수 있는 대시보드를 만드는 것이 목표

- Windows: 개발 및 테스트 환경
- Linux(Rocky): 실제 운영 및 실습 환경
- OS 간 코드 호환성 유지 (psutil 기반)

<br>

## 기능
### 1. 시스템 리소스 모니터링
- CPU 사용률
- RAM 사용량
- Disk 사용량
- 서버 업타임

### 2. 서비스 상태 확인
- nginx / docker 등 주요 서비스 상태
- Linux: systemctl is-active
- Windows: 미지원 안내 처리

### 3. 로그 모니터링
- Linux 로그 파일 tail (최근 N줄)
- 콘솔 스타일 UI로 표시
- 접근 권한 및 민감 정보 고려

### 4. 프로세스 분석 (확장 핵심 기능)
- 실행 중인 프로세스 목록
- 프로세스별 정보 수집
  - 프로세스명 / PID
  - 실행 경로
  - CPU / 메모리 사용량
  - 실행 사용자
  - 열린 포트
- 위험 요소 자동 판단
  - root/관리자 권한 실행
  - 외부 공개 포트
  - 과도한 메모리 사용
  - 비정상 실행 경로
- 프로세스 역할 설명(Explain)

<br>

## 기술 스택
| 영역         | 기술                            |
| ---------- | ----------------------------- |
| OS         | Rocky Linux 9 / Windows       |
| Backend    | FastAPI                       |
| 시스템 정보     | psutil                        |
| 서비스 상태     | systemctl (Linux)             |
| 템플릿        | Jinja2                        |
| Front UI   | HTML + CSS (Retro / Pixel 콘솔) |
| DB         | SQLite (확장 예정)                |
| Web Server | Nginx (Reverse Proxy)         |

<br>

## 프로젝트 특징
- psutil 기반 Cross Platform 설계
- Linux 서비스(systemctl)와 로그 직접 연동
- 단순 수치 → 의미 기반 상태 분석
- Retro / Pixel 콘솔 UI로 서버 관리 감성 강화
- FastAPI 기반 가벼운 모니터링 서버 
- 운영 서버 기준 실전 구조

> 이 프로젝트는 단순한 모니터링 도구가 아니라    
> 서버 운영 관점에서 “판단을 돕는 UI”를 목표로 한다.

<br>

## 프로젝트 전체 그림
```
[ Rocky Linux 서버 ]
        |
        |  (psutil / systemctl / 로그 / 프로세스)
        v
[ FastAPI 백엔드 ]
        |
        |  JSON / Template
        v
[ 웹 대시보드 (Retro Console UI) ]
        |
        v
[ Nginx Reverse Proxy ]

```

<br>

## 디렉토리 구조
```
server-monitor/
├── docs/
│   ├── POLICY.md # 프로세스 보안 분석 규칙
├── web/
│   ├── app/
│   │   ├── main.py          # FastAPI 엔트리
│   │   ├── constants/
│   │   │   ├── ports.py
│   │   │   ├── processes.py
│   │   │   └── windows.py
│   │   ├── system/
│   │   │   ├── cpu.py
│   │   │   ├── memory.py
│   │   │   ├── disk.py
│   │   │   ├── uptime.py
│   │   │   ├── service.py
│   │   │   ├── log.py
│   │   │   └── process.py   # (확장) 프로세스 분석
│   │   ├── templates/
│   │   │   └── dashboard.html
│   │   └── static/
│   │       └── style.css
│   ├── db/
│   │   └── monitor.db
│   ├── requirements.txt
│   └── README.md            # 개발/실습용 문서
├── .gitignore
└── README.md                # 프로젝트 소개 문서

```
<br>

### FastAPI 서버를 실행할 때마다 가상환경(venv) 실행
```
[ 내 PC 전체 Python ]
        |
        |  (venv 켜기)
        v
[ server-monitor 전용 Python ]
```
- venv를 안 켜면 FastAPI가 존재하지 않음

#### * 실행 루틴 (window)
```
# 1. 프로젝트 폴더 이동
cd web

# 2. 가상환경 활성화
venv\Scripts\activate

# 3. 서버 실행
uvicorn app.main:app --reload
```

---

<br>

## 기능 범위 
### ✅ 1차 완성 목표 (완료)
- CPU 사용률
- RAM 사용량
- Disk 사용량
- 서버 구동 시간
- nginx / docker 서비스 상태
- 로그 tail (최근 10줄)
- 기본 대시보드 (Retro / Pixel Server Console)

<br>
<img src="./images/window_1_task.png" width="600" >

> Windows 개발 환경에서 1차 목표 기능을 구현한 화면

<br>

### 🔜 확장 목표
- 프로세스 위험 분석
- 포트 기반 보안 경고
- Docker 컨테이너 인식
- 다중 서버 관리
- Slack / Telegram 알림
- Prometheus 연계
  
<br>
<img src="./images/window_2_task.png" width="600" >

> Windows 개발 환경에서 프로세스 위험 분석을 구현한 화면

---

<br>

## 개발 순서

1. 구조 / README / 컨셉 정리 ✅
2. Windows에서 기능 구현 ✅
   - process.py 설계 (Windows / Linux 분기 기준)
   - 경고 판단 로직을 순수 함수로 분리
3. UI 작업 (process 추가) ✅
4. Git push ✅
5. Rocky Linux에서 pull
6. OS 차이로 깨지는 부분 수정
7. 운영 테스트