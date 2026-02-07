# Ansible 기반 운영 환경 구성 (infra)

> 본 문서는 **운영 환경 자동화의 기준이나 정책을 정의하지 않는다.**  
> Ansible을 어떻게 설계했는지에 대한 **구조적 이해를 돕기 위한 안내 문서**이다.

---
<br>

## 📑 목차

- [Ansible 디렉토리 구조](#ansible-디렉토리-구조)
- [Ansible 적용 단계](#ansible-적용-단계)
- [Ansible과 프로젝트의 경계 요약](#ansible과-프로젝트의-경계-요약)
- [Ansible 사용을 위한 초기 준비 절차 (Bootstrap)](#ansible-사용을-위한-초기-준비-절차-bootstrap)
- [이후 작업](#이후-작업)
- [이 문서의 범위](#이-문서의-범위)

---
<br>

## Ansible 디렉토리 구조
```
infra/ansible/
├── ansible.cfg
├── inventory/
│   ├── dev.ini
│   ├── prod.ini
│   └── group_vars/
│       ├── all.yml          # OS / 환경 공통 (항상 로드)
│       ├── dev.yml          # 개발 환경 (dev.ini 사용 시 로드)
│       └── prod.yml         # 운영 환경 (prod.ini 사용 시 로드)
├── playbooks/
│   ├── setup.yml        # 서버 기본 세팅
│   ├── docker.yml       # Docker 설치
│   └── monitoring.yml   # server-monitor 배치
├── roles/
│   ├── common
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── vars/
│   │       └── main.yml
│   ├── docker
│   └─ security
│       └─ tasks/
│           └── main.yml
```
- common : OS 공통
- security : 보안
- docker : 컨테이너
- monitoring : 앱 배치

---
<br>

## Ansible 적용 단계

### 1. 서버 기본 준비
- python3, pip
- git
- firewalld
- 기본 유틸 (procps, iproute)

<br>

### 2. 보안 기본 설정
- root SSH 로그인 차단
- 운영 계정 생성
- SSH 키 배포
- firewalld 기본 포트 설정

| 포트   | 용도                 |
| ---- | --------------------- |
| 22   | SSH                   |
| 80   | Nginx                 |
| 443  | HTTPS                 |
| 8000 | 내부 FastAPI (외부 차단 가능) |

<br>

### 3. Python 실행 환경 구성
- /opt/server-monitor/venv 생성
- requirements.txt 설치
- OS별 psutil 빌드 대응 (gcc, python3-devel)

<br>

### 4. systemd 서비스 등록

> Ansible은 FastAPI 애플리케이션을 systemd 서비스로 등록한다.   
> ※ 아래 systemd 유닛은 예시이며, 실제 값은 Ansible 템플릿에서 관리한다.

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

## Ansible 사용을 위한 초기 준비 절차 (Bootstrap)
> Ansible은 “이미 준비된 서버”가 아니라 아무것도 없는 서버를 운영 상태로 끌어올리기 위한 도구   
> 즉, 최소한의 부트스트랩 절차가 필요

### 1. Git 저장소 구성 원칙 (Inventory 관리)

#### 원칙
1. 실제 서버 IP / 계정 정보는 Git에 직접 커밋하지 않는다
2. dev.ini, prod.ini는 환경별 로컬 파일

#### 적용 방식
```
infra/ansible/inventory/
├── dev.ini          # ❌ git 제외
├── prod.ini         # ❌ git 제외
├── dev.ini.example  # ⭕ 커밋
└── prod.ini.example # ⭕ 커밋
```
#### dev.ini.example 예시
- 실제 IP / 계정은 각 환경에서 .example을 복사해 직접 작성
```
[servers]
dev-server ansible_host= ansible_user=
```

<br>

### 2. 관리 대상 서버에서 Git 저장소 가져오기

> Ansible은 **컨트롤 노드(local PC)**에서 실행되지만,   
> 운영 서버에서도 구성과 문서를 동일하게 확인 가능해야 한다.

#### Rocky Linux 서버
```
sudo dnf install -y git

cd ~
git clone https://github.com/seoheejung/server-monitor.git
cd server-monitor/infra/ansible
```
- 서버에는 inventory 파일만 로컬에서 생성
- playbook / role / 문서는 Git 기준으로 동기화

<br>

### 3. Rocky Linux에 Ansible 설치

#### Rocky Linux 9 기준
```
sudo dnf install -y epel-release
sudo dnf install -y ansible-core
```

#### 설치 확인
```
ansible --version

# ansible [core 2.14.18]
```

#### 권장 사항
1. Ansible은 시스템 패키지로 설치
2. venv 안에 설치하지 않음 (운영 도구이기 때문)

<br>

### 4. Inventory 파일 생성 (서버별)
```
cd infra/ansible/inventory
cp dev.ini.example dev.ini
```
- ansible_user는 이미 존재하는 SSH 계정
- 서비스 계정(server-monitor)은 Ansible이 생성

#### 최초 연결 확인
```
# 비밀번호 방식 허용 (임시용)
ansible all -m ping -i inventory/dev.ini --ask-pass
```
#### 성공 시
```
dev-server | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```
- SSH 키 인증 성공
- Ansible 실행 성공 
- Python 인터프리터 자동 감지 성공 (/usr/bin/python3)
- 네트워크 / 계정 / 권한 문제 없음
  
> 이 단계가 실패하면 **Ansible 이전의 문제(SSH, 계정, 네트워크)**로 판단

<br>

### 5. Ansible 컬렉션 경로 초기화
- Ansible Core 2.10+부터 다수의 시스템 제어 모듈은 core에서 제거되고 Collection 단위로 분리되었다.
- Ansible 설치 직후, 컬렉션 저장 경로를 명시적으로 준비해야 한다.
- Rocky Linux에서 ansible-core만 설치한 초기 상태에서는 컬렉션을 설치할 기본 경로가 존재하지 않을 수 있다.

#### 사용자 영역 컬렉션 경로 생성
```
mkdir -p ~/.ansible/collections
```
- Ansible 실행 사용자 기준
- sudo 불필요
- 사용자별 실행 환경 분리 가능

> 이 디렉토리가 없으면 `ansible-galaxy collection install` 실행 시   
> 설치 경로를 찾지 못해 실패한다.

<br>

### 6. 필수 Ansible 컬렉션 설치

- 운영 서버 기본 제어에 필요한 모듈(`firewalld`, `selinux`, `authorized_key` 등)은 `ansible.posix` 컬렉션에 포함되어 있다.

#### 필수 컬렉션 설치
```
ansible-galaxy collection install ansible.posix \
  --collections-path ~/.ansible/collections
```

#### 설치 확인
```
ansible-galaxy collection list --collections-path ~/.ansible/collections
```

#### 정상 출력 예시
```
Collection    Version
------------- -------
ansible.posix 2.1.0
```

> 이 단계가 누락되면 couldn't resolve module/action 'firewalld' 와 같은 오류가 발생한다.

<br>

#### 7. ansible.cfg 설정 (roles / collections 경로 고정)

- 컬렉션과 roles를 설치했더라도, Ansible이 해당 경로를 명시적으로 인식하지 못하면 실행에 실패한다.

#### `infra/ansible/ansible.cfg`
```
[defaults]
inventory = ./inventory
roles_path = ./roles
collections_paths = ~/.ansible/collections:/usr/share/ansible/collections
```

- `roles_path`: playbooks 하위가 아닌 상위 roles/ 디렉토리 사용
- `collections_paths`: 사용자 컬렉션 우선, 시스템 전역 컬렉션 fallback
- 실행 디렉토리 기준 상대 경로 사용

> 이 설정이 없을 경우 컬렉션을 설치했더라도 모듈을 찾지 못하는 문제가 발생할 수 있다.

#### 컬렉션 모듈 사용 원칙
- Ansible 2.14 기준, 컬렉션 모듈은 FQCN(Fully Qualified Collection Name) 사용을 원칙으로 한다.

#### `roles/common/tasks/main.yml`
```
- name: Open SSH port
  ansible.posix.firewalld:
    port: 22/tcp
    permanent: true
    state: enabled
    immediate: true
```

#### `roles/common/handlers/main.yml`
```
---
- name: Reload firewalld
  ansible.builtin.service:
    name: firewalld
    state: reloaded

```

<br>

### 8. 서버 기본 상태 구성 실행
```
cd /home/rockylinux/server-monitor/infra/ansible

ansible-playbook playbooks/setup.yml -i inventory/dev.ini

# SSH 키 대신 비밀번호 입력 (임시)
ansible-playbook playbooks/setup.yml \
  -i inventory/dev.ini \
  --ask-pass \
  --ask-become-pass

```
#### 완료 로그
```
PLAY RECAP *******************************************************************************
dev-server                 : ok=8    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```


#### Bootstrap 단계 전체 요약
1. Git 저장소 clone
2. inventory 파일 로컬 생성
3. ansible-core 설치
4. 컬렉션 경로 생성 
5. 필수 컬렉션 설치 (ansible.posix)
6. ansible.cfg 설정
7. ansible ping 테스트
8. setup.yml 실행

#### 이 단계에서 수행되는 것
1. 필수 패키지 설치
2. firewalld 활성화
3. SSH 포트 설정
4. 서비스 계정 생성
5. /opt/server-monitor 디렉토리 생성
6. Python venv 구성

---
<br>

## 이후 작업

### 1. 애플리케이션 배치 자동화 확장
- `monitoring.yml` 기준 배치 로직 고도화
  - Git clone / pull 전략 정리
  - requirements.txt 변경 감지 시 venv 재구성 여부 판단
- FastAPI 실행 옵션 표준화
  - worker 수
  - log level
  - 실행 사용자 고정

<br>

### 2. systemd 서비스 운영 안정화
- systemd unit 템플릿 분리 및 변수화
- restart 정책 세분화
  - 실패 횟수 기준
  - 재시작 간격
- journalctl 로그 수집 범위 정의

<br>

### 3. 네트워크 및 프록시 구성
- Nginx Reverse Proxy 연동
  - 외부 포트 노출 최소화
  - FastAPI 내부 포트 보호
- HTTPS 적용 (Let’s Encrypt 또는 내부 인증서)
- firewalld 규칙 점검 자동화 여부 검토

<br>

### 4. 운영 환경 분리
- dev / prod inventory 분리 강화
- group_vars 기준 환경별 설정 차등 적용
- 테스트 서버 → 운영 서버 전환 시 재현성 검증

<br>

### 5. 관측 및 운영 보조 도구 연계 (선택)
- 로그 수집기 연동 여부 검토
- 메트릭 수집(Prometheus 등) 도입 가능성 검토
- 장애 발생 시 Ansible 재적용 기준 명확화

---
<br>

## 이 문서의 범위

- `infra/` 디렉토리 하위 Ansible 구성의 전체 구조 개요
- inventory / playbook / role 간 역할 분리와 책임 범위
- 운영 서버 환경 구성을 위한 Ansible 적용 흐름 요약
- 초기 서버 상태에서 Ansible을 적용하기 위한 Bootstrap 절차 정리

> ※ 운영 서버 환경 자동화 기준 및 재현 전략: docs/ANSIBLE_INFRA.md 참조  
> ※ FastAPI 애플리케이션 설계 및 역할: docs/FASTAPI_DEV.md 참조  
> ※ Linux Native 실행 검증: docs/NATIVE_RUN.md 참조  
> ※ 프로세스 보안 정책 및 판단 기준: docs/POLICY.md 참조

---
