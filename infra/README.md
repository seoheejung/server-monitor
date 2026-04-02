# Ansible 기반 운영 환경 구성 (infra)

> 본 문서는 **운영 환경 자동화의 기준이나 정책을 정의하지 않는다.**  
> Ansible을 어떻게 설계했는지에 대한 **구조적 이해를 돕기 위한 안내 문서**이다.

---
<br>

## 📑 목차

- [Ansible 디렉토리 구조](#ansible-디렉토리-구조)
- [Ansible 적용 단계](#ansible-적용-단계)
- [Ansible 배포 적용 순서](#ansible-배포-적용-순서)
- [Ansible과 프로젝트의 경계](#ansible과-프로젝트의-경계)
- [Ansible 사용을 위한 초기 준비 절차 (Bootstrap)](#ansible-사용을-위한-초기-준비-절차-bootstrap)
- [로컬 검증 방법](#로컬-검증-방법)
- [이후 작업](#이후-작업)
- [이 문서의 범위](#이-문서의-범위)

---
<br>

## Ansible 디렉토리 구조
```
infra/ansible/
├── ansible.cfg
├── inventory/
│   ├── local.ini
│   ├── dev.ini              # 로컬 생성 (Git 제외)
│   ├── prod.ini             # 로컬 생성 (Git 제외)
│   └── group_vars/
│       └── all/
│           ├── main.yml     # 공통 변수
│           └── vault.yml    # 로컬 생성 + Ansible Vault 암호화 + Git 제외
├── playbooks/
│   ├── setup.yml            # 서버 기본 세팅
│   ├── docker.yml           # Docker 설치
│   └── server_monitor.yml   # server-monitor 배치
├── roles/
│   ├── common/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── vars/
│   │       └── main.yml
│   ├── server_monitor/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── templates/
│   │   │   ├── server-monitor.service.j2
│   │   │   └── app.env.j2
│   │   └── vars/
│   │       └── main.yml
│   ├── docker/
│   ├── security/
│   │   └── tasks/
│   │       └── main.yml
│   ├── mongodb/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── templates/
│   │       └── mongod.conf.j2
│   ├── nginx/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── templates/
│   │       └── nginx.conf.j2
```
- common : OS 공통 설정
- security : 보안 설정
- docker : 컨테이너 환경 구성
- server_monitor : 앱 배치 및 서비스 구성
- mongodb : MongoDB 설치, 인증 활성화, 사용자 계정 관리

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

### 4. Vault 변수 파일 생성

```bash
cd infra/ansible/inventory/group_vars/all
cp vault.yml.example vault.yml
ansible-vault encrypt vault.yml
```
- 이 작업은 Ansible을 실행하는 로컬(컨트롤 노드)에서 수행한다.
- vault.yml은 MongoDB 관리자 비밀번호와 앱 계정 비밀번호를 저장한다.
- vault.yml은 Git에 커밋하지 않으며, 로컬에서 생성 후 Ansible Vault로 암호화하여 사용한다.

<br>


### 5. 데이터 저장소 구성
- MongoDB 설치 (repo 등록 포함)
- mongod 서비스 활성화
- systemd 기반 자동 실행
- MongoDB는 애플리케이션 판단 기준 저장소로 사용
- MongoDB는 인증(`authorization`)이 활성화된 상태로 운영
- MongoDB는 `127.0.0.1` 바인딩을 기본으로 하여 외부 직접 접근을 차단
- 관리자 계정과 애플리케이션 계정을 분리하여 생성
- 애플리케이션은 전용 DB 계정을 사용하여 접근
- 비밀번호 및 민감 정보는 Ansible Vault로 관리

<br>

### 6. 네트워크 및 프록시 구성
- Nginx reverse proxy 구성
- FastAPI 포트(8000)는 외부에서 접근 불가
- firewalld 기반 외부 접근 제어
- 모든 요청은 Nginx를 통해서만 전달
- reverse proxy를 통해 서비스 경로를 분리 가능 (/monitor, /other 등)

<br>

### 7. systemd 서비스 등록

> Ansible은 FastAPI 애플리케이션을 systemd 서비스로 등록한다.   
> ※ 아래 systemd 유닛은 예시이며, 실제 값은 Ansible 템플릿에서 관리한다.

- 부팅 시 자동 실행
- 비정상 종료 시 재시작
- 로그 systemd 관리

```
[Unit]
Description=Server Monitor
After=network.target mongod.service
Requires=mongod.service

[Service]
User=server-monitor
Group=server-monitor
WorkingDirectory=/opt/server-monitor/app
EnvironmentFile=/opt/server-monitor/app/.env
ExecStart=/opt/server-monitor/venv/bin/uvicorn main:app --host ${HOST} --port ${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

---

## Ansible 배포 적용 순서

### 전체 순서
```
common → security → mongodb → nginx → server_monitor
```

<br>

### common role
1. server-monitor 그룹 생성  
2. server-monitor 사용자 생성  
3. 기본 패키지 설치 (python3, pip, git 등)  
4. `/opt/server-monitor` 루트 디렉토리 생성  
5. `logs`, `data`, `scripts` 하위 디렉토리 생성  
6. Python virtualenv 생성 (`/opt/server-monitor/venv`)  
7. 디렉토리 소유권 및 권한 설정  

<br>

### security role
1. root SSH 로그인 비활성화  
2. 운영 계정 SSH 접근 허용 설정  
3. SSH 키 기반 인증 설정  
4. firewalld 활성화  
5. 기본 포트 허용 (22, 80, 443, 필요 시 8000)  
6. 불필요 포트 차단  

<br>

### mongodb role
1. MongoDB repository 등록  
2. MongoDB 패키지 설치  
3. mongod.conf(auth disabled) 배포
4. mongod 시작 
5. 관리자 계정 생성  
6. 애플리케이션 계정 생성  
7. mongod.conf(auth enabled) 재배포
8. mongod 재시작
9. admin auth 검증

<br>

### nginx role
1. Nginx 패키지 설치  
2. nginx 설정 파일 배치 (`nginx.conf`)  
3. FastAPI upstream 설정 정의 (서비스 실행 전 설정)
4. reverse proxy 경로 설정  
5. 서비스 daemon reload  
6. nginx 서비스 enable 및 started 보장  

<br>

### server_monitor role
1. 배포 디렉토리 생성  
2. 소스 코드 복사 (`/home/rockylinux/server-monitor/web/app → /opt/server-monitor/app`)  
3. requirements 설치 (venv 기준)  
4. `.env` 파일 배치  
5. systemd unit 파일 배치  
6. daemon reload 수행  
7. service enable 및 started/restarted 상태 보장  

---
<br>

## Ansible과 프로젝트의 경계

| 구분    | 책임        |
| ----- | ----------- |
| OS 상태 | Ansible     |
| 실행 환경 | Ansible     |
| 코드 동작 | FastAPI     |
| 판단 기준 | MongoDB     |
| 위험 분석 | psutil + 로직 |
| 운영 정책 | 코드 + 데이터  |
---
<br>

## Ansible 사용을 위한 초기 준비 절차 (Bootstrap)
> Ansible은 최소 SSH 접속과 권한 확보가 된 초기 서버를 운영 상태로 끌어올리기 위한 도구

### 1. Git 저장소 구성 원칙 (Inventory 관리)

#### 원칙
1. 실제 서버 IP / 계정 정보는 Git에 직접 커밋 금지
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

### 7. ansible.cfg 설정 (roles / collections 경로 고정)

- roles와 collections 경로를 명시적으로 지정하면 실행 환경 차이로 인한 탐색 문제를 줄일 수 있다.

#### `infra/ansible/ansible.cfg`
```
[defaults]
inventory = ./inventory
roles_path = ./roles
collections_path = ~/.ansible/collections:/usr/share/ansible/collections
```

- `roles_path`: playbooks 하위가 아닌 상위 roles/ 디렉토리 사용
- `collections_paths`: 사용자 컬렉션 우선, 시스템 전역 컬렉션 fallback
- 실행 디렉토리 기준 상대 경로 사용

> 이 설정이 없더라도 기본 경로에서 동작할 수 있다.   
> 다만 프로젝트 내 roles/collections 경로를 명시적으로 고정하지 않으면   
> 실행 환경에 따라 모듈 또는 role 탐색 결과가 달라질 수 있다.

#### 컬렉션 모듈 사용 원칙
- Ansible 2.14 기준, 컬렉션 모듈은 FQCN(Fully Qualified Collection Name) 사용을 권장한다.

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

## 로컬 검증 방법
### 1. 컨테이너 실행
```
docker compose build
docker compose up -d
docker compose exec ansible sh
```
### 2. 정적 검증
```
chmod 755 /workspace

ansible-lint .
ansible-playbook -i inventory/local.ini playbooks/setup.yml --syntax-check
ansible-playbook -i inventory/local.ini playbooks/server_monitor.yml --syntax-check
```

### 3. 연결 확인
```
ansible all -i inventory/local.ini -m ping
```

---
<br>

## 이후 작업

### 1. 애플리케이션 배치 자동화 확장
- Git clone / pull 전략 정리
- requirements.txt 변경 감지 시 venv 재구성 여부 판단
- FastAPI 실행 옵션 표준화
  - worker 수
  - log level
  - 실행 사용자 고정

<br>

### 2. systemd 서비스 운영 안정화
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

### 4. 관측 및 운영 보조 도구 연계 (선택)
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
