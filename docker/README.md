# server-monitor Docker & 운영 가이드

이 문서는 server-monitor 프로젝트를  
**Rocky Linux 운영 환경 및 Docker 컨테이너에서 안정적으로 실행하기 위한 설계 기록**이다.

---
<br>

## 1. Docker 도입 목적
- FastAPI + psutil 기반 서버 모니터링을 실행 환경 차이 없이 사용하기 위함
- Rocky Linux / 테스트 서버 / 향후 클라우드 환경을 동일한 방식으로 관리
- systemd에 의존하지 않고 서비스 실행
- 이후 운영 자동화 및 확장을 고려한 구조

---
<br>

## 2. 기본 전제

- 이 컨테이너는 서버 모니터링 용도로 사용된다.
- **read-only 모니터링 목적**이며,
  컨테이너 내부에서 서버 상태를 변경하지 않는다
- 서버 상태 조회를 위해 아래 정보에 접근할 수 있어야 한다:
  - /proc : 프로세스, CPU, 메모리 정보
  - /sys : 일부 시스템 정보 (선택)
  - 네트워크 정보 (--net=host 사용 시)
- 실제 접근 범위는 **Docker 실행 옵션에 따라 결정된다**

---
<br>

## 3. OS 차이 대응 설계 요약

### 서비스 상태
- Linux: `systemctl is-active`
- Docker 컨테이너 환경:
  - systemctl 미지원
  - 해당 항목은 `unknown`으로 표시
  - 오류가 아닌 **환경 차이로 인한 정보 제한**으로 처리

### 로그 접근
- `/var/log` 접근 제한 고려
- 권한 부족 시: `[PERMISSION DENIED]` 표시
- sudo 실행 금지 (운영 안전성)

### 프로세스 & 포트
- `psutil` 기반으로 프로세스 정보 수집
- 다른 사용자 소유 프로세스의 포트 정보는 접근 실패 고려
- 실패 시 처리 방식
  - `ports: []`
  - 경고로 처리하지 않음
  - 권한 제한으로 판단

---
<br>

## 4. Docker 실행 전략

### 권장 실행 방식 (서버 모니터링)

```bash
docker run -d \
--name server-monitor \
-p 8000:8000 \
--pid=host \
--net=host \
-v /proc:/host/proc:ro \
-v /var/log:/var/log:ro \
server-monitor:latest
```
- 관리자용 모니터링 도구로 사용
- 일반 웹 서비스보다 높은 권한이 필요함
- `--net=host` 사용 시 -p 옵션은 의미 없음
- 테스트/운영 시나리오에 따라 선택

---
<br>

## 5. Docker 파일 구성

### docker/.dockerignore
- 이미지 용량 감소와 보안을 위해 불필요한 파일을 제외

```dockerignore
venv/
__pycache__/
*.pyc
.git
.gitignore
.env
docs/
images/
```

### docker/Dockerfile
#### 구성 방향
- Rocky Linux 환경 기준 동작 확인
- psutil 정상 동작
- FastAPI + uvicorn 기반
- systemctl 사용하지 않음
- 가능한 단순한 구성 유지

  
```
FROM python:3.11-slim

LABEL maintainer="server-monitor"
LABEL description="Server Monitoring Dashboard (FastAPI + psutil)"

# 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리
WORKDIR /app

# 필수 패키지 설치 (psutil, proc 접근용)
# systemctl 사용하지 않음 (컨테이너 환경 고려)
RUN apt-get update && \
    apt-get install -y \
        procps \
        iproute2 \
    && rm -rf /var/lib/apt/lists/*

# requirements 복사 및 설치
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY web/app ./app

# 포트
EXPOSE 8000

# FastAPI 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

---
<br>

## 6. 빌드 & 실행 테스트
### 이미지 빌드
```
docker build -t server-monitor -f docker/Dockerfile .
```

### 테스트 실행
```
docker run -p 8000:8000 server-monitor
```

### 운영 실행 (권한 포함)
```
docker run -d \
  --name server-monitor \
  --pid=host \
  --net=host \
  -v /proc:/proc:ro \
  -v /var/log:/var/log:ro \
  server-monitor
```

---
<br>

## 7. Docker 기반 Rocky Linux 서버 준비

> 기본 동작 확인은 Docker 기반 Rocky Linux에서 수행하고,
> 최종 검증은 VirtualBox 기반 Rocky Linux Native 환경에서 진행한다.


### Docker rockylinux 설치 및 실행
```
docker run -it -p 2222:8000 --name rocky-93 rockylinux:9.3 /bin/bash
# docker exec -it rocky-93 /bin/bash
```

### 기본 패키지 설치
```
# 패키지 목록 업데이트
sudo dnf update -y

# 필요한 도구 설치 (시스템 정보 수집에 필요한 패키지 등)
sudo dnf install -y vim procps-ng iproute
```

### Python 환경 확인
```
python3 --version
git --version

# 없다면 설치
sudo dnf install -y python3 python3-pip git
```

### 프로젝트 준비
```
mkdir -p ~/projects
cd ~/projects
git clone <레포주소>
cd server-monitor/web
```

### 로그 환경 준비 (Docker 환경 기준)
> Docker 컨테이너에는 기본 로그 데몬이 없을 수 있음
> log.py는 파일 직접 접근 방식이므로 로그 파일 존재가 필요
```
# 컨테이너 내부에서 확인할 경우 로그 서비스를 설치하고 실행
sudo dnf install -y rsyslog

# 서비스 수동 시작
/usr/sbin/rsyslogd  

# 파일 생성 완료
ls /var/log/messages 

# 테스트 로그 생성
nohup sh -c 'while true; do logger -t [INFO] "System Health Check OK"; sleep 5; done' &
tail /var/log/messages
```

---
<br>

## 8. Docker 기반 Rocky Linux 가상환경 생성

### 1. venv 설치
- Windows venv는 Linux에서 사용 불가 ⚠️
- Linux 서버에서는 반드시 새로 생성 필요
```
python3 -m venv venv
source venv/bin/activate

# 확인
(venv) [user@rocky server-monitor]$
```

### 2. 미리 정의해둔 Python 패키지 설치
```
pip install -r requirements.txt
```

#### psutil 빌드 에러 발생 시
```
sudo dnf install -y gcc python3-devel
pip install psutil
```
> psutil은 이 프로젝트의 핵심 의존성
> 여기서 실패하면 Docker 이전에 반드시 해결해야 함

---
<br>

## 9. FastAPI Native 실행

### FastAPI 서버 실행
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 0.0.0.0 : 외부 접속 허용
- 8000 : 테스트 포트

### 서버 내부 확인
```
curl http://localhost:2222
```

### 외부 접속 확인 (브라우저)
```
http://localhost:2222
```
- HTML 대시보드가 출력되면 FastAPI + 네트워크 정상

---
<br>
