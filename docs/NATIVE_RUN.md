# Rocky Linux 네이티브 실행 & 사전 검증

> Docker를 적용하기 전에, Rocky Linux 환경에서 FastAPI + psutil 조합이 정상 동작하는지 확인 필요
> 문제 원인을 OS / Python / Docker로 명확히 분리하기 위한 필수 절차


## 목적
### Docker를 먼저 적용하면 다음 원인이 섞여 버린다:
- Rocky Linux 환경 문제
- Python / psutil 빌드 문제
- systemctl / /proc / 권한 접근 문제
- Docker volume / namespace 문제

### 네이티브 실행을 먼저 검증 필요
- Rocky Linux + psutil + FastAPI 순수 조합 확인
- 시스템 접근 가능 여부 명확
- Docker는 단순 재현 단계로 남김

---
<br>

## 1단계 목표
- FastAPI 서버 정상 기동
- psutil 기반 시스템 정보 정상 수집
- /proc, 프로세스, 포트 접근 가능 여부
- 서비스 상태 판단을 위한 최소 조건 확인
- Rocky Linux 네이티브 실행이 끝나면 아래 사항을 진행
  - Docker
  - systemd 서비스 등록
  - 보안 옵션 (read-only FS 등)
 
---
<br>

## 1. Rocky Linux 서버 준비

> Docker의 Rocky Linux 컨테이너로 먼저 진행 후 virtualBox Rocky Linux 진행
>
### Docker rockylinux 설치 및 실행
```
docker run -it -p 2222:8000 --name rocky-93 rockylinux:9.3 /bin/bash
# docker exec -it rocky-93 /bin/bash
```

### VirtualBox rockylinux 서버 접속
```
ssh user@서버IP

```

### Rocky Linux에서 dnf 사용하기
```
# 패키지 목록 업데이트
dnf update -y

# 필요한 도구 설치 예시
dnf install -y vim procps-ng
```

### 필수 패키지 확인
```
python3 --version
git --version
```

- 없다면 설치
```
sudo dnf install -y python3 python3-pip git
```

- 추가로 시스템 정보 수집에 필요한 패키지
```
sudo dnf install -y procps-ng iproute
```

### 프로젝트 위치 준비
```
mkdir -p ~/projects
cd ~/projects
git clone <레포주소>
cd server-monitor/web
```

---
<br>

## 2. Rocky Linux 가상환경 생성

### ⚠️ Windows venv는 Linux에서 사용 불가
- 운영 서버에서는 반드시 새로 생성
```
python3 -m venv venv
source venv/bin/activate

# 확인
(venv) [user@rocky server-monitor]$
```

### Python 패키지 설치
```
pip install -r requirements.txt
```
- psutil 빌드 에러 발생 시
```
sudo dnf install -y gcc python3-devel
pip install psutil
```
> psutil은 이 프로젝트의 핵심 의존성
> 여기서 실패하면 Docker 이전에 반드시 해결해야 함

---
<br>

## 3. FastAPI 네이티브 실행

### FastAPI 서버 실행
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 0.0.0.0 : 외부 접속 허용
- 8000 : 테스트 포트

### 서버 내부 확인
```
# docker
curl http://localhost:2222

# virtualBox
curl http://localhost:8000
```

### 외부 접속 확인 (브라우저)
```
# virtualBox
http://서버IP:8000/

# docker
http://localhost:2222

```
- `ip addr`로 IP 확인
- JSON 응답이 나오면 FastAPI + 네트워크 정상

---
<br>

## 4. 방화벽 설정 (Rocky Linux)
### 포트 개방 (영구)
```
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### 적용 여부 확인
```
sudo firewall-cmd --list-ports
```
- 8000/tcp 가 출력되어야 함

### 재부팅 후에도 유지되는지 확인
```
sudo reboot

# 재접속 후

sudo firewall-cmd --list-ports
```
`--permanent` 옵션을 사용했기 때문에 Rocky Linux 재부팅 이후에도 포트는 유지

---
<br>

## 5. psutil 동작 검증
- Python REPL에서 직접 확인
```
python
```
```
import psutil

psutil.cpu_percent(interval=1)
psutil.virtual_memory()
psutil.disk_partitions()
list(psutil.process_iter(['pid', 'name']))
```
- 확인 포인트
    - 값이 0 / None / 예외 없이 정상 출력되는지
    - 프로세스 목록이 실제 서버와 일치하는지

---
<br>

## 6. 서비스 상태 판단 전략 (네이티브 기준)
- systemctl 결과 참고

### 권장 최소 판단 기준
- nginx → 프로세스 존재 여부
- mysql → 포트 리스닝 여부
- docker → 프로세스 + 소켓 존재 여부

> systemctl은 Docker 환경에서 제한될 수 있으므로 프로세스 / 포트 기반 판단이 핵심

---
<br>

## 7. 이 단계가 끝나면 가능한 것
- 필요한 OS 패키지
- Python 의존성
- psutil 접근 범위
- 권한 이슈 여부
- /proc, 포트, 프로세스 접근 가능 여부
