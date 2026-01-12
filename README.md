# 서버 관리형 프로젝트 : 서버 상태 모니터링 대시보드
#### Rocky Linux 서버의 상태를 수집해서 웹으로 보여주는 프로젝트
Rocky Linux 서버의 시스템 리소스(CPU, 메모리, 디스크),   
주요 서비스 상태(systemctl), 로그 정보를 수집하여   
웹 대시보드로 시각화하는 서버 모니터링 시스템   

## 기능
- CPU / RAM / Disk 사용량
- 서버 업타임
- 특정 프로세스 상태 (nginx, docker 등)
- 로그 파일 tail 보기

## 기술 스택
| 영역         | 선택                |
| ---------- | ----------------- |
| OS         | Rocky Linux 9     |
| Backend    | FastAPI           |
| 시스템 정보     | psutil            |
| 서비스 상태     | systemctl         |
| DB         | SQLite            |
| Front      | Jinja2 (HTML 템플릿) |
| Web Server | Nginx             |


## 프로젝트 특징
- Rocky Linux 환경에서 시스템 리소스를 직접 수집
- psutil과 systemctl을 활용한 서버 상태 모니터링
- Linux 로그 파일 직접 분석
- Nginx Reverse Proxy 구성
- FastAPI를 사용하여 비동기 기반의 가벼운 서버 모니터링 API 구성


## 프로젝트 전체 그림
```
[ Rocky Linux 서버 ]
        |
        |  (psutil / systemctl / 로그 읽기)
        v
[ FastAPI 백엔드 ]
        |
        |  JSON API
        v
[ 간단한 웹 대시보드 ]
        |
        v
[ Nginx Reverse Proxy ]
```

## 기능 범위 
### ✅ 1차 완성 목표 (필수)
- CPU 사용률
- RAM 사용량
- Disk 사용량
- 서버 업타임
- nginx / docker 서비스 상태
- 로그 tail (최근 10줄)

## 디렉토리 구조
```
server-monitor/
│        web/
│        ├── app/
│        │   ├── main.py          # FastAPI 엔트리
│        │   ├── __init__.py
│        │   ├── system/
│        │   │   ├── __init__.py
│        │   │   ├── cpu.py
│        │   │   ├── memory.py
│        │   │   ├── disk.py
│        │   │   ├── uptime.py
│        │   │   ├── service.py
│        │   │   └── log.py
│        │   ├── templates/
│        │   │   └── dashboard.html
│        │   └── static/
│        │       └── style.css
│        ├── db/
│        │   └── monitor.db
│        ├── requirements.txt
│        └── README.md
├──.gitignore        
└── README.md

```

## 핵심 기능 구현 방향
### CPU / RAM / Disk
- psutil.cpu_percent()
- psutil.virtual_memory()
- psutil.disk_usage('/')

### 서버 구동 시간
- /proc/uptime 읽기
- 또는 psutil.boot_time()

### 서비스 상태
```
systemctl is-active nginx
systemctl is-active docker
```
- Python에서 subprocess로 실행
- systemctl 실행 시 권한 문제를 고려하여 sudo 설정 또는 실행 사용자 분리
- 결과: active / inactive / failed

### 로그 tail
```
/var/log/nginx/access.log
/var/log/messages
```
- 최근 N줄만 읽기
- 파일 직접 읽기 (tail 구현)
- 로그 파일 접근 시 권한 제한 및 민감 정보 노출 방지 고려

## 웹 화면
### dashboard.html 예시 구성
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

## Nginx 연동
- FastAPI → 8000
- Nginx → 80
- Reverse Proxy 설정

## 추천 작업 순서
1. FastAPI 실행 확인
2. CPU / RAM API
3. Disk / Uptime
4. systemctl 서비스 상태
5. 로그 tail
6. HTML 대시보드
7. Nginx 연동

## 확장 가능성
- 다중 서버 모니터링
- Slack / Telegram 알림 연동
- Docker 컨테이너 리소스 모니터링
- Prometheus 연계
