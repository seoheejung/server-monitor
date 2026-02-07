# Ansible 기반 운영 환경 자동화 설계

> 프로젝트에서 Rocky Linux를 기준으로 Ansible을 운영 환경 재현 도구로 사용하는 것을 정의하는 문서

> Ansible은 자동화 도구로 운영 환경을 하나의 ‘코드 상태’로 구현하는 장치로 사용

---
<br>

## 📑 목차

- [Ansible 도입 배경](#ansible-도입-배경)
- [Ansible의 역할 정의](#ansible의-역할-정의)
- [Ansible 사용 철학](#ansible-사용-철학)
- [서버 배포 기준 디렉토리](#서버-배포-기준-디렉토리)
- [Ansible 적용 단계](#ansible-적용-단계)
- [Ansible 디렉토리 구조](#ansible-디렉토리-구조)
- [Ansible과 프로젝트의 경계 요약](#ansible과-프로젝트의-경계-요약)
- [운영 장애 시 Ansible 재적용 시나리오](#운영-장애-시-ansible-재적용-시나리오)
- [Ansible 사용을 위한 초기 준비 절차 (Bootstrap)](#ansible-사용을-위한-초기-준비-절차-bootstrap)
- [운영자 퀵 가이드 (Cheatsheet)](#운영자-퀵-가이드-cheatsheet)


---
<br>

## Ansible 도입 배경

- OS (Windows / Rocky Linux)
- 런타임 (Native / Docker)
- 권한 모델 (root / non-root)
- 서비스 관리 방식 (systemd / container)

> Ansible은 운영 환경을 “증명 가능하게 고정”하기 위한 필수 구성 요소

### Ansible 동작 방식 
```
local PC (컨트롤 노드)
   |
   |  SSH
   ↓
서버 (관리 대상 노드)
```
- 에이전트 없음
- SSH로 명령 실행
- YAML 파일에 “원하는 상태”를 적음
- Ansible이 현재 상태 <-> 원하는 상태를 비교해서 필요한 작업만 수행

> 서버를 다시 설치해도, 같은 조건의 운영 환경을 사람 손 개입 없이 재현 가능

---
<br>

##  Ansible의 역할 정의

### 1. Ansible이 담당하는 것
- 서버의 상태를 **만드는** 역할

| 구분       | 내용                      |
| -------- | ----------------------- |
| OS 기본 세팅 | 패키지 설치, 타임존, 로케일        |
| 사용자      | 운영 계정 생성, sudo 권한       |
| 보안       | SSH 설정, firewalld 기본 정책 |
| 런타임      | Python, venv, Docker    |
| 실행 환경    | FastAPI 실행 기반 준비        |
| 서비스 등록   | systemd 서비스 등록/활성화      |

### 2. Ansible이 관여하지 않는 것
- 판단 로직에 관여 불가

| 영역                      | 이유           |
| ----------------------- | ------------ |
| FastAPI 내부 코드           | 앱 책임         |
| psutil 분석 로직            | 코드 책임        |
| 프로세스 위험 판단              | MongoDB + 로직 |
| 정책 기준 (KNOWN_PROCESSES) | 데이터 책임       |
| UI / 템플릿                | 프론트 책임       |

---
<br>

## Ansible 사용 철학

### 1. 서버 재설치 = 동일 상태 복구

- 서버 OS 재설치
- 새 VM 생성
- 테스트 서버 → 운영 서버 전환
- Ansible 보장 범위
    ```
    Ansible 실행
         ↓
    동일한 패키지
    동일한 디렉토리 구조
    동일한 서비스 상태
    동일한 실행 방식
    ```

### 2. 운영자는 “Ansible만 실행”

- 패키지 하나하나 설치
- 방화벽 수동 설정
- systemd 파일 수동 작성
- venv 직접 activate

위 작업을 하지 않고 **Ansible Playbook 실행만 수행**

---
<br>

## 서버 배포 기준 디렉토리

### Ansible이 기준으로 삼는 운영 서버 구조
```
/opt/server-monitor/
├── app/        # FastAPI 코드
├── venv/       # Python 가상환경
├── logs/       # 애플리케이션 로그
├── data/       # DB / 런타임 데이터
├── scripts/    # 실행 스크립트
```

- /opt : 서비스성 애플리케이션 표준 위치
- Docker / Native / systemd 공통 유지 가능
- 운영 서버 이식 시 경로 고정

---
<br>

## Ansible 적용 단계

### 1. 서버 기본 준비

- python3, pip
- git
- firewalld
- 기본 유틸 (procps, iproute)

### 2. 보안 기본 설정

- root SSH 로그인 차단
- 운영 계정 생성
- SSH 키 배포
- firewalld 기본 포트 설정
- 
| 포트   | 용도                 |
| ---- | --------------------- |
| 22   | SSH                   |
| 80   | Nginx                 |
| 443  | HTTPS                 |
| 8000 | 내부 FastAPI (외부 차단 가능) |


### 3. Python 실행 환경 구성
- /opt/server-monitor/venv 생성
- requirements.txt 설치
- OS별 psutil 빌드 대응 (gcc, python3-devel)

### 4. systemd 서비스 등록

> Ansible은 FastAPI를 서비스로 등록한다.   
> > ※ 아래 systemd 유닛은 예시이며, 실제 값은 Ansible 템플릿에서 관리한다.

- 부팅 시 자동 실행
- 비정상 종료 시 재시작
- 로그 systemd 관리

```
[Unit]
Description=Server Monitor
After=network.target

[Service]
ExecStart=/opt/server-monitor/venv/bin/uvicorn app.main:app
WorkingDirectory=/opt/server-monitor/app
Restart=always

[Install]
WantedBy=multi-user.target
```

---
<br>

## Ansible 디렉토리 구조
```
infra/ansible/
├── inventory/
│   ├── dev.ini
│   └── prod.ini
├── group_vars/
│   ├── all.yml          # OS / 환경 공통
│   ├── linux.yml        # Rocky Linux 계열
│   ├── windows.yml     # Windows 전용
│   ├── dev.yml          # 개발 환경
│   └── prod.yml         # 운영 환경
├── playbooks/
│   ├── setup.yml        # 서버 기본 세팅
│   ├── docker.yml       # Docker 설치
│   ├── monitoring.yml  # server-monitor 배치
├── roles/
│   ├── common
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── vars/
│   │       └── main.yml
│   ├── docker
│   ├─ security
│   │   └─ tasks/
└   └       └── main.yml
```
- common : OS 공통
- security : 보안
- docker : 컨테이너
- monitoring : 앱 배치

### 변수 관리의 분리 (Group Vars)

> 플레이북 분기 없이 변수로만 해결하기 위해 변수 분리

- 환경 차이(Dev / Prod)
- OS 차이 (Rocky Linux / Windows)
- 런타임 차이 (Native / Docker)

| 구분    | 위치                       | 예시                       |
| ----- | ------------------------ | ------------------------ |
| 전역 공통 | `group_vars/all.yml`     | 앱 경로, 포트, 서비스명           |
| OS 차이 | `group_vars/linux.yml`   | dnf 패키지, systemd         |
|       | `group_vars/windows.yml` | win_feature, win_package |
| 환경 차이 | `group_vars/dev.yml`     | DEBUG, 테스트 포트            |
|       | `group_vars/prod.yml`    | 보안 옵션, 운영 포트             |


---
<br>

## Ansible과 프로젝트의 경계 요약

| 구분    | 책임          |
| ----- | ----------- |
| OS 상태 | Ansible     |
| 실행 환경 | Ansible     |
| 코드 동작 | FastAPI     |
| 판단 기준 | MongoDB     |
| 위험 분석 | psutil + 로직 |
| 운영 정책 | 코드 + 데이터    |

---
<br>

## 운영 장애 시 Ansible 재적용 시나리오

> 장애 발생 시 문제 원인을 “고쳐서 유지”하지 않고,   
> 환경을 다시 만들어 정상 상태로 복귀하는 전략 적용

### 1. 전제 원칙
- 운영 서버는 수동 수정 대상이 아님
- 장애 대응 시 해당 서버를 고치지 않고 다시 새로운 서버를 생성

### 2. Ansible 재적용이 필요한 대표 시나리오

#### 서버 재설치 / VM 재생성
- OS 크래시
- 스토리지 손상
- 테스트 서버 → 운영 서버 신규 전환

```
OS 설치
   ↓
Ansible 실행
   ↓
동일 환경 복구
```
- 코드 / 정책 / 설정은 Git + MongoDB 기준으로 복원
- 운영자 개입 없음

#### 운영 중 환경 위험 신호 감지
- 수동으로 설치된 패키지
- 임의로 수정된 systemd 서비스
- 방화벽 포트가 문서와 불일치
- venv 내부 라이브러리 버전 불일치
-  대응 전략
  
| 선택지         | 판단   |
| ----------- | ---- |
| 수동 수정       | ❌ 금지 |
| Ansible 재실행 | ✅ 기본 |
| 서버 재생성      | ✅ 가능 |

#### 서비스 실행 불능 (FastAPI / systemd)
- systemd 서비스가 반복 실패
- FastAPI 실행 경로 깨짐
- venv 손상
- psutil 빌드 오류
- 대응 절차
  1. FastAPI 로그 확인 (systemd)
  2. 코드 자체 문제 아님 확인
  3. Ansible monitoring.yml 재적용
  4. 실패 시 → 서버 재구성 판단

### 3. 장애 원인 분리 기준

| 분류     | 판단                 |
| ------ | ------------------ |
| 코드 문제  | FastAPI / psutil   |
| 데이터 문제 | MongoDB            |
| 환경 문제  | OS / 패키지 / systemd |

> 환경 문제로 판단되면 즉시 Ansible 재적용

### 4. Ansible 재적용 범위 전략

#### 부분 재적용
- 패키지 누락
- 서비스 파일 손상
- 방화벽 설정 불일치
```
ansible-playbook playbooks/monitoring.yml
```

#### 전체 재적용
- 서버 상태 신뢰 불가
- 누적 수동 수정 의심
- 운영 이력 불명확
```
ansible-playbook playbooks/setup.yml
ansible-playbook playbooks/security.yml
ansible-playbook playbooks/monitoring.yml
```

#### 서버 폐기 + 재생성
- 다음 조건 중 하나라도 해당되면 서버 재생성 권장
  1. OS 레벨 문제
  2. root 권한 오염
  3. 보안 사고 의심
  4. 재현 불가 상태

> 새 서버 + Ansible

### 5. Ansible 기반 운영의 핵심 이점

- 장애 복구 시간이 분 단위
- 환경 상태가 문서와 항상 일치
- “누가 언제 뭘 고쳤는지” 추적 불필요
- 운영자 숙련도 의존 최소화

---
<br>

## Ansible 사용을 위한 초기 준비 절차 (Bootstrap)
> Ansible은 “이미 준비된 서버”가 아니라 아무것도 없는 서버를 운영 상태로 끌어올리기 위한 도구   
> 즉, 최소한의 부트스트랩 절차가 필요

### 1. Git 저장소 구성 원칙 (Inventory 관리)
- 원칙
  1. 실제 서버 IP / 계정 정보는 Git에 직접 커밋하지 않는다
  2. dev.ini, prod.ini는 환경별 로컬 파일

- 적용 방식
```
infra/ansible/inventory/
├── dev.ini          # ❌ git 제외
├── prod.ini         # ❌ git 제외
├── dev.ini.example  # ⭕ 커밋
└── prod.ini.example # ⭕ 커밋
```

- .gitignore 예시
```
# Ansible inventory (real environments)
infra/ansible/inventory/*.ini
!infra/ansible/inventory/*.example
```

- dev.ini.example 예시
  - 실제 IP / 계정은 각 환경에서 .example을 복사해 직접 작성
```
[servers]
dev-server ansible_host= ansible_user=
```

### 2. 관리 대상 서버에서 Git 저장소 가져오기

> Ansible은 **컨트롤 노드(local PC)**에서 실행되지만,   
> 운영 서버에서도 구성과 문서를 동일하게 확인 가능해야 한다.

#### Rocky Linux 서버
```
sudo dnf install -y git
git clone https://github.com/<your-repo>.git
cd <your-repo>/infra/ansible
```
- 서버에는 inventory 파일만 로컬에서 생성
- playbook / role / 문서는 Git 기준으로 동기화

### 3. Rocky Linux에 Ansible 설치

- Rocky Linux 9 기준
```
sudo dnf install -y epel-release
sudo dnf install -y ansible-core
```

- 설치 확인
```
ansible --version

# ansible [core 2.14.18]
```

- 권장 사항
1. Ansible은 시스템 패키지로 설치
2. venv 안에 설치하지 않음 (운영 도구이기 때문)

### 4. Inventory 파일 생성 (서버별)
```
cd infra/ansible/inventory
cp dev.ini.example dev.ini
```
- ansible_user는 이미 존재하는 SSH 계정
- 서비스 계정(server-monitor)은 Ansible이 생성

### 5. 최초 연결 확인
```
ansible all -m ping -i inventory/dev.ini
```
- 성공 시
```
dev-server | SUCCESS => {
    "ping": "pong"
}
```

> 이 단계가 실패하면 **Ansible 이전의 문제(SSH, 계정, 네트워크)**로 판단

### 6. 서버 기본 상태 구성 실행
```
ansible-playbook playbooks/setup.yml -i inventory/dev.ini
```

#### 이 단계에서 수행되는 것
1. 필수 패키지 설치
2. firewalld 활성화
3. SSH 포트 설정
4. 서비스 계정 생성
5. /opt/server-monitor 디렉토리 생성
6. Python venv 구성
   
---
<br>

## 운영자 퀵 가이드 (Cheatsheet)

### 1. 전체 환경 점검
```
ansible all -m ping -i inventory/prod.ini
```

### 2. 보안 설정 및 기본 세팅
```
ansible-playbook playbooks/setup.yml -i inventory/prod.ini
```

### 3. 모니터링 앱만 재배포
```
ansible-playbook playbooks/monitoring.yml -i inventory/prod.ini --tags "deploy"
```

### 4. 특정 서버만 복구
```
ansible-playbook ... -l [hostname]
```