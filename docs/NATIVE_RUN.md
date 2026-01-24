# Rocky Linux 네이티브 실행 검증

> Rocky Linux 네이티브 환경에서의 동작 검증 기록

<b>
본 단계는 단순 배포 실험이 아니라 <br>
서버 모니터링 로직이 OS 환경(Rocky Linux)에서 실제로 어떻게 동작하는지를 <br>
코드 단위로 검증하기 위한 필수 절차이다.
</b>

<br>

<b>
특히 psutil / systemctl / /proc / 권한 제약이 <br>
실제 운영 환경에서 어떤 한계를 가지는지를 명확히 분리하여 확인한다
</b>

---
<br>

## Rocky Linux 선택 기준 (VirtualBox 기준)
### 1. OS 선택 기준
- RHEL 계열 운영체제
- systemd / firewalld 기본 포함
- /proc 기반 정보 접근 가능
- 운영 서버와 동일한 프로세스 관리 구조

### 2. 버전 기준 (9.0 사용)
- Rocky Linux 9.x 계열 기준 사용
- 마이너 버전 차이는 검증 대상 아님
- 초기 환경 구성 및 재현성 우선
- VirtualBox 이미지 확보 용이
- Python / psutil 빌드 검증 안정성 확보
- 마이너 버전 업그레이드가 검증 결과에 영향 없음

### 3. 가상화 환경 선택
- VirtualBox VM 사용
- 물리 서버 없이 서버 환경 재현
- 고정 IP 설정 가능
- firewalld 기반 포트 제어 가능
- Docker 적용 이전 OS 레벨 동작 분리 검증

---

<br>

## 목적

### 1. Rocky Linux + psutil + FastAPI 순수 네이티브 실행 검증
- Docker, systemd, 보안 옵션 적용 이전 단계
- “이 코드가 OS에서 가능한가?”를 먼저 증명

### 2. 시스템 접근 가능 범위 확인
- /proc 기반 프로세스 / 포트 수집 가능 여부
- 로그 파일 직접 접근 가능 여부
- systemctl 사용 가능 여부 및 fallback 로직 검증

### 3. Python / psutil 의존성 검증
- psutil 빌드 성공 여부
- root / non-root 실행 시 차이 확인

## 검증 환경 정보

- OS: Rocky Linux 9.x
- 커널: 기본 제공 커널 (VirtualBox Guest)
- Python: 3.x (dnf 패키지 기준)
- 실행 사용자:
  - 기능 검증: root
  - 권한 차이 검증: 일반 사용자
- 실행 방식:
  - Docker 컨테이너 (기능/로직 1차 검증)
  - VirtualBox 네이티브 (운영 제약 2차 검증)

---
<br>

## [1단계 목표] 네이티브 실행 검증 범위 (완료)
### 1. FastAPI
- FastAPI 서버 정상 기동
- HTML 템플릿 + static 파일 정상 렌더링

### 2. 시스템 자원 수집
- CPU / Memory / Disk / Uptime 정상 수집
- Linux 기준 디스크(/) 사용률 정상 계산

### 3. 프로세스 & 포트
- psutil 기반 프로세스 목록 수집
- 프로세스별 포트 정보 수집 가능 여부
- root / 일반 사용자 권한 차이 확인

### 4. 로그
- `/var/log/messages` tail 가능 여부
- Linux 전용 기능 정상 동작 확인

### 5. 서비스 상태
- `systemctl` 사용 가능 시 → `systemctl` 결과
- `systemctl` 불가 시 → psutil 기반 `fallback` 정상 동작
 
---
<br>

## 환경 설계

### 1. 디렉토리 기반 배포 구조

> 운영 서버 기준 구조를 유지하기 위해 코드, 로그, 데이터, 실행 스크립트 분리

```
/opt/server-monitor/
├── app/ # FastAPI 애플리케이션
├── venv/ # Python 가상환경
├── logs/ # 애플리케이션 로그
├── data/ # sqlite / 런타임 데이터
└── scripts/ # 실행·관리 스크립트
```
- `/opt`는 서비스성 애플리케이션 배포에 일반적으로 사용
- Docker / systemd 여부와 무관하게 유지 가능한 구조
- 운영 서버 환경과 동일한 배포 패턴 유지

### 2. 네트워크 및 접근 전략

- VirtualBox Host-Only 네트워크 사용  
  → 개발 PC ↔ VM 간 안정적인 접근

- 고정 IP 할당  
  → 서비스 주소 고정 및 포트 단위 접근 제어 검증

- firewalld 기반 포트 제어  
  → 필요한 포트만 개방하여 운영 서버 보안 조건 유지

---
<br>

## Rocky Linux 서버 준비

> 기본 동작 확인은 Docker 기반 Rocky Linux에서 수행하고,
> 최종 검증은 VirtualBox 기반 Rocky Linux 네이티브 환경에서 진행한다.


### 1. Docker rockylinux 설치 및 실행
```
docker run -it -p 2222:8000 --name rocky-93 rockylinux:9.3 /bin/bash
# docker exec -it rocky-93 /bin/bash
```

### 1-1. VirtualBox rockylinux 서버 접속
```
ssh user@서버IP
```

### 2. 기본 패키지 설치
```
# 패키지 목록 업데이트
sudo dnf update -y

# 필요한 도구 설치 (시스템 정보 수집에 필요한 패키지 등)
sudo dnf install -y vim procps-ng iproute
```

### 3. Python 환경 확인
```
python3 --version
git --version

# 없다면 설치
sudo dnf install -y python3 python3-pip git
```

### 4. 프로젝트 준비
```
mkdir -p ~/projects
cd ~/projects
git clone <레포주소>
cd server-monitor/web
```

### 5. 로그 환경 준비 (Docker 환경 기준)
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

## Docker vs Native 환경 차이 요약

| 항목 | Docker 컨테이너 | VirtualBox 네이티브 |
|----|----|----|
| systemctl | 사용 불가 | 사용 가능 |
| PID 1 | bash / tini | systemd |
| 로그 | 직접 파일 생성 필요 | 기본 로그 데몬 존재 |
| 목적 | 로직 검증 | 운영 적합성 검증 |

---
<br>

## Rocky Linux 가상환경 생성

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

## FastAPI 네이티브 실행

### 1. FastAPI 서버 실행
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- 0.0.0.0 : 외부 접속 허용
- 8000 : 테스트 포트

### 2. 서버 내부 확인
```
# Docker
curl http://localhost:2222

# VirtualBox
curl http://localhost:8000
```

### 3. 외부 접속 확인 (브라우저)
```
# VirtualBox
http://서버IP:8000/

# Docker
http://localhost:2222

```
- `ip addr`로 IP 확인
- HTML 대시보드가 출력되면 FastAPI + 네트워크 정상

---
<br>

## 4. 방화벽 설정 (VirtualBox Rocky Linux)
### 포트 개방 (영구)
```
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### 적용 확인
```
sudo firewall-cmd --list-ports
```
- 8000/tcp 가 출력되어야 함

### 재부팅 후 유지 확인
```
sudo reboot

# 재접속 후
sudo firewall-cmd --list-ports
```
`--permanent` 옵션을 사용했기 때문에 Rocky Linux 재부팅 이후에도 포트 유지

---
<br>

## psutil 동작 검증
### 1. Python REPL 직접 테스트
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
### 2. 확인 포인트
- 예외 없이 값이 반환되는지
- /proc 접근 오류가 발생하지 않는지
- 프로세스 목록이 실제 서버와 일치하는지

### 권한별 동작 차이 요약

| 항목 | root 실행 | 일반 사용자 실행 |
|----|----|----|
| 프로세스 목록 | 전체 수집 | 일부 제한 |
| 포트 정보 | 전체 수집 | 타 사용자 프로세스 누락 가능 |
| 로그 접근 | 가능 | PermissionError 가능 |
| systemctl | 가능 | 제한적 |

---
<br>

## 코드 기준 OS 의존 동작 정리
### 1. 디스크 (disk.py)
- Linux: `/` 기준 사용률
- Windows: `C:\\`
- OS 분기 처리 완료

### 2. 로그 (log.py)
- Linux 전용
- 파일 직접 tail 방식
- systemd / journalctl 미사용

### 3. 프로세스 (process.py)
- psutil 기반 전수 수집
- 프로세스별 포트 수집 (proc.connections)
- root 미실행 시 포트 누락 가능 (정상)

### 4. 서비스 상태 (service.py)
- systemctl 가능 → `systemctl is-active`
- systemctl 불가 → psutil 프로세스 존재 여부
- Docker / 컨테이너 환경 fallback 정상

---
<br>

## 서비스 상태 판단 전략 (네이티브 기준)
### 1. systemctl 결과 참고
- systemctl은 Docker 환경에서 제한될 수 있으므로 프로세스 / 포트 기반 판단이 핵심
  
### 2. 권장 최소 판단 기준
- nginx → 프로세스 존재 여부
- mysql → 포트 리스닝 여부
- Docker → 프로세스 + 소켓 존재 여부
