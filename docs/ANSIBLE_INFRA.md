# 운영 서버 환경 자동화 표준 (Ansible)

> 본 문서는 운영 서버의 OS 상태와 실행 환경을 코드로 재현하기 위한 자동화 기준을 정의한다.   
> 애플리케이션 내부 동작, 실행 로직, 판단 기준은 다루지 않는다.

---
<br>

## 📑 목차

- [Ansible 도입 배경](#ansible-도입-배경)
- [Ansible의 역할 정의](#ansible의-역할-정의)
- [Ansible 사용 철학](#ansible-사용-철학)
- [서버 배포 기준 디렉토리](#서버-배포-기준-디렉토리)
- [운영 장애 시 Ansible 재적용 시나리오](#운영-장애-시-ansible-재적용-시나리오)
- [운영자 퀵 가이드 (Cheatsheet)](#운영자-퀵-가이드-cheatsheet)
- [이 문서의 범위](#이-문서의-범위)

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

#### Ansible은 자동화 도구로 운영 환경을 하나의 ‘코드 상태’로 구현하는 장치로 사용

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
/
├── opt/
│   └── server-monitor/
│       ├── app/        ← FastAPI 코드 (git clone 대상)
│       ├── venv/       ← Ansible이 생성
│       ├── logs/       ← 런타임 데이터
│       ├── data/
│       └── scripts/
│
├── home/
│   └── rockylinux/
│       └── ansible-repo/   ← Ansible 리포지토리
│           └── infra/ansible/
```

| 구분              | 위치                              |
| --------------- | ------------------------------- |
| 운영 대상 (FastAPI) | `/opt/server-monitor`           |
| 운영 도구 (Ansible) | `/home/rockylinux/ansible-repo` |

- `/opt/server-monitor/` → Ansible만 변경
- `/home/` → 운영자 작업 공간

---
<br>

## 운영 장애 시 Ansible 재적용 시나리오

> 장애 발생 시 문제 원인을 “고쳐서 유지”하지 않고,   
> 환경을 다시 만들어 정상 상태로 복귀하는 전략 적용

### 1. 전제 원칙
- 운영 서버는 수동 수정 대상이 아님
- 장애 대응 시 해당 서버를 고치지 않고 다시 새로운 서버를 생성

<br>

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

<br>

### 3. 장애 원인 분리 기준

| 분류     | 판단                 |
| ------ | ------------------ |
| 코드 문제  | FastAPI / psutil   |
| 데이터 문제 | MongoDB            |
| 환경 문제  | OS / 패키지 / systemd |

> 환경 문제로 판단되면 즉시 Ansible 재적용

<br>

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

<br>

### 5. Ansible 기반 운영의 핵심 이점

- 장애 복구 시간이 분 단위
- 환경 상태가 문서와 항상 일치
- “누가 언제 뭘 고쳤는지” 추적 불필요
- 운영자 숙련도 의존 최소화

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

---
<br>

## 이 문서의 범위

- 운영 서버의 OS 상태 및 실행 환경 자동화 기준
- 서버 재현성 확보를 위한 Ansible 설계 원칙
- 서비스 등록, 보안 기본 설정, 런타임 구성

> ※ 애플리케이션 내부 구조 및 로직: docs/FASTAPI_DEV.md 참조  
> ※ Linux Native 실행 검증: docs/NATIVE_RUN.md 참조  
> ※ 프로세스 판단 기준 및 정책: docs/POLICY.md 참조
> ※ 인프라 디렉토리 구성 및 자동화 구조: infra/README.md 참조
> 
---
