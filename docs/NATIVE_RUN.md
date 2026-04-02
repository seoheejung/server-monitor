# Rocky Linux Native 실행 검증

> 본 문서는 서버 모니터링 애플리케이션이  
> Rocky Linux Native 환경에서 Ansible을 통해 정상적으로 동작하는지를 검증하기 위한 실행·환경 검증 기준을 정의한다.  
> 애플리케이션 설계, 운영 자동화, 정책 판단 기준은 다루지 않는다.


<br>

psutil / systemctl / /proc / 권한 제약이 <br>
실제 운영 환경에서 어떤 한계를 가지는지를 명확히 분리하여 확인

---
<br>

## 📑 목차

  - [Rocky Linux 선택 기준 (VirtualBox 기준)](#rocky-linux-선택-기준-virtualbox-기준)
  - [목적](#목적)
  - [검증 환경 정보](#검증-환경-정보)
  - [[1단계 목표] Native 실행 검증 범위](#1단계-목표-native-실행-검증-범위)
  - [[2단계 목표] Ansible 배포 후 Native 실행 검증](#2단계-목표-ansible-배포-후-native-실행-검증)
  - [전체 실행 순서](#전체-실행-순서)
  - [환경 설계](#환경-설계)
  - [Docker vs Native 환경 차이 요약](#docker-vs-native-환경-차이-요약)
  - [코드 기준 OS 의존 동작 정리](#코드-기준-os-의존-동작-정리)
  - [서비스 상태 판단 전략 (Native 기준)](#서비스-상태-판단-전략-native-기준)
  - [이 문서의 범위](#이-문서의-범위)
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

### 1. Rocky Linux + psutil + FastAPI 순수 Native 실행 검증
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
  - VirtualBox Native (운영 제약 2차 검증)

---
<br>

## [1단계 목표] Native 실행 검증 범위
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

## [2단계 목표] Ansible 배포 후 Native 실행 검증
### 1. 사전 준비
#### Git 설치
- 최소 OS 패키지 설치
```
# OS 패키지 업데이트
sudo dnf update -y

# Python 3 설치 (venv, pip 포함)
sudo dnf install -y python3 python3-venv python3-pip

# Git 설치
sudo dnf install -y git

# epel-release 설치 (Ansible 설치 전)
sudo dnf install -y epel-release

# Ansible 설치
sudo dnf install -y ansible-core
```
- 레포 클론 경로: /home/rockylinux/server-monitor/
```
git clone <repo_url> /home/rockylinux/server-monitor/
```

### 2. Ansible 배포
#### 레포 경로에서 Ansible 실행
```
cd /home/rockylinux/server-monitor/infra/ansible

# 서버 기본 구성
ansible-playbook -i inventory/local.ini playbooks/setup.yml

# server-monitor 배치
ansible-playbook -i inventory/local.ini playbooks/server_monitor.yml
```
#### 결과 확인
- 오류 없이 완료
- /opt/server-monitor/ 구조 정상 생성
- Python venv 설치 및 패키지 설치 확인
- systemd 서비스 유닛 등록 확인
> 참고: setup.yml 실행 시 SSH 키 및 sudo 권한 확인 필요

### 3. Native 환경 실행 검증
#### 서비스 시작/상태 확인
```
systemctl status server-monitor
systemctl is-enabled server-monitor
systemctl is-active server-monitor

ss -tunlp | grep 8000
curl http://127.0.0.1:8000/
journalctl -u server-monitor -n 100 --no-pager
```
#### FastAPI 접속 확인
- 브라우저에서 http://<server_ip>:<port>/ 접속
- HTML/Static 정상 렌더링
#### OS 의존 기능 확인
- /proc 기반 프로세스/포트 수집
- /var/log/messages tail 가능
- psutil 기반 CPU/Memory/Disk/Uptime 수집
- root / non-root 실행 시 차이 확인
#### 네트워크 및 포트 확인
- firewall-cmd --list-ports로 서비스 포트 확인
- 고정 IP 접근 테스트

### 4. MongoDB 인증 검증
#### 관리자 계정 로그인 확인
```
mongosh -u <admin_user> -p <admin_password> --authenticationDatabase admin
```
- 로그인 성공 체크
- Authentication failed 로그 발생 시 비정상
#### 애플리케이션 계정 로그인 확인
```
mongosh -u <app_user> -p <app_password> --authenticationDatabase process_monitor
```
- 로그인 성공 체크
- Authentication failed 로그 발생 시 비정상
#### 인증 없이 접속 차단 확인
```
mongosh
```
- 권한 오류가 발생 체크
#### 애플리케이션 DB 연결 확인
- systemd 서비스 실행 이후 .env에 설정된 MONGO_URL 기준으로 DB 연결을 검증한다.
- MongoDB 연결 오류가 발생하지 않아야 한다.
#### systemd 실행 후 검증
```
systemctl restart server-monitor
journalctl -u server-monitor -n 100 --no-pager
```
- MongoDB 인증 오류 (Authentication failed)가 없어야 한다.

### 5. 검증 체크 리스트
| 항목                  | 확인 방법                     | 정상 기준            |
| ------------------- | ------------------------- | ---------------- |
| FastAPI 서버 기동       | systemctl / curl          | 200 OK, HTML 렌더링 |
| CPU / Memory / Disk | psutil 스크립트               | 값 수집 가능          |
| 프로세스 목록             | psutil                    | 실행 프로세스 확인       |
| 포트 수집               | psutil.connections        | root 기준 모든 포트 확인 |
| 로그 tail             | tail -f /var/log/messages | 로그 출력 정상         |
| 서비스 상태              | systemctl is-active       | active           |
| 포트 방화벽              | firewall-cmd              | 필요한 포트만 열림       |
| systemd 자동 시작       | systemctl is-enabled      | enabled          |
| MongoDB 관리자 인증      | mongosh -u <admin> --authenticationDatabase admin | 로그인 성공 |
| MongoDB 앱 계정 인증     | mongosh -u <app> --authenticationDatabase process_monitor | DB 접근 가능 |
| MongoDB 무인증 차단      | mongosh                   | 인증 없이 접근 불가 |
| MongoDB 앱 연결        | systemd 실행 후 journalctl 확인 | 인증 오류 없음 |

---
<br>

## 전체 실행 순서

### 1단계

VirtualBox Rocky Linux 9.x 준비

### 2단계

레포 clone

```
git clone <repo_url> /home/rockylinux/server-monitor
cd /home/rockylinux/server-monitor/infra/ansible
```

### 3단계

Ansible 적용

```
ansible-playbook -i inventory/local.ini playbooks/setup.yml
ansible-playbook -i inventory/local.ini playbooks/server_monitor.yml
```

### 4단계

MongoDB 인증 확인

- 관리자 계정 로그인 성공
- 앱 계정 로그인 성공
- 무인증 접속 차단

### 5단계

systemd 서비스 검증

- 서비스 재기동 성공
- 상태가 active 인지 확인
- journalctl 기준 오류 로그 없는지 확인
- 앱 `.env` 기준 DB 연결 성공

```
systemctl enable server-monitor
systemctl restart server-monitor
systemctl status server-monitor

journalctl -u server-monitor -n 100 --no-pager
```

### 6단계

애플리케이션 접속 검증

```
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/dashboard/summary
```

### 7단계

Native 기능 검증

- `/proc` 기반 프로세스 수집
- root / 일반 사용자 차이
- `/var/log/messages` tail
- `systemctl` 상태 조회
- 포트/방화벽 확인

### 8단계

운영 기준 최종 확인

```
firewall-cmd --list-ports
ss -tunlp | grep 8000
systemctl is-enabled server-monitor
systemctl is-active server-monitor
```

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

## Docker vs Native 환경 차이 요약

| 항목 | Docker 컨테이너 | VirtualBox Native |
|----|----|----|
| systemctl | 사용 불가 | 사용 가능 |
| PID 1 | bash / tini | systemd |
| 로그 | 직접 파일 생성 필요 | 기본 로그 데몬 존재 |
| 목적 | 로직 검증 | 운영 적합성 검증 |

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

## 서비스 상태 판단 전략 (Native 기준)
### 1. systemctl 결과 참고
- systemctl은 Native 환경에서 서비스 상태 판단의 기준으로 사용
  
### 2. 권장 최소 판단 기준
- nginx → 프로세스 존재 여부
- mysql → 포트 리스닝 여부
- Docker → 프로세스 + 소켓 존재 여부

---
<br>

## 이 문서의 범위

- Rocky Linux Native 환경에서의 실행 가능성 검증
- psutil / systemctl / /proc 기반 OS 의존 동작 확인
- 권한(root / non-root)에 따른 동작 차이 검증

> ※ 애플리케이션 구조 및 설계 의도: docs/FASTAPI_DEV.md 참조  
> ※ 운영 환경 자동화: docs/ANSIBLE_INFRA.md 참조  
> ※ 프로세스 보안 정책: docs/POLICY.md 참조

---
