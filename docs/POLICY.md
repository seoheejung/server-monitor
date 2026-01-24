# 🔐 프로세스 보안 분석 규칙 (Process Analysis Policy)

> 운영 서버 환경에서 프로세스를 분석·진단·제어하기 위한 보안 판단 기준과 정책 규칙 정의

## 문서 구조

1. 프로세스 분석 정책 (Analysis / Warning / Diagnosis)
     - 위험 판단 기준
     - 경고 분류
     - 상태 코드(OK / WARN / DANGER)
     -  정렬·표시 로직

2. 프로세스 종료 정책 (Termination / Control)
     - 종료 대상 판단
     - Soft / Hard Kill
     - 시스템 보호

3. MongoDB 기반 종료 정책
   - 기본 원칙
   - 차단 규칙
   - 우선 순위

---
<br>

## [1] 프로세스 분석 정책

### 분석 설계 원칙

#### 1. 데이터 중심 분석
- 수집 단계에서 OS 정보를 확정하여 데이터 객체에 포함하며, 분석 단계는 외부 환경이 아닌 오직 전달된 데이터(Dict)만을 기반으로 판단
- 동일한 프로세스 데이터에 대해 동일한 분석 결과 보장

#### 2. 위험 우선순위 (Risk Hierarchy)
- 권한(`username`), 네트워크(`ports`), 실행 경로(`exe`)를 최우선 위험 요소로 간주
- CPU/메모리 점유율은 시스템 장애 가능성을 시사하는 보조 지표로 활용

#### 3. 화이트리스트 기반 예외 처리
- 시스템 필수 프로세스에 대한 오탐을 방지하기 위해 `KNOWN_PROCESSES` 및 `WINDOWS_SYSTEM_PROCS` 등의 화이트리스트 정책을 적용
  
---

### 위험 판단 기준 (Warning Rules)

#### 위험 레벨 기준
- 🟡 INFO : 즉각적 위험 없음 (관찰 대상)
- 🟠 WARN : 설정/권한/노출 점검 필요
- 🔴 DANGER : 보안 또는 시스템 위험 가능성 높음

#### 1. RUNNING_AS_ADMIN
- root, SYSTEM, Administrator 권한 실행
- Windows PID 4 제외
- 위험 레벨 : 🟠 

#### 2. PUBLIC_PORT(n)
- KNOWN_PORTS에 정의된 주요 서비스 포트를 해당 역할과 무관한 프로세스가 점유하여 외부 접근을 허용하는 경우
- PUBLIC_PORT는 항상 Warning으로 기록되며, INFO/WARN 구분은 UI 해석 단계에서 결정
- 위험 레벨 : 🟡 / 🟠 

#### 3. SYSTEM_PORT(n)
- 비표준 시스템 포트 개방
- `port < 1024` (단, `KNOWN_PORTS` 및 `WINDOWS_SYSTEM_PORTS` 제외)
- 위험 레벨 : 🔴 

#### 4. HIGH_MEMORY_USAGE
- 메모리 사용률 ≥ 20%
- 서비스 장애, 메모리 릭 가능성 점검 필요
- HIGH_MEMORY_USAGE는 perf_warnings로 분리되며 상태 판정(OK/WARN/DANGER)에는 영향을 주지 않는다
- 위험 레벨 : 🟡 

#### 5. SUSPICIOUS_PATH
- 표준 실행경로 외 위치에서 실행
- 악성코드 / 수동 배포 바이너리 탐지 목적
- 조건부 허용 경로 실행 시: 🟠 
- 비표준 경로 실행 시: 🔴 

---

### Windows 전용 정책

#### 1. 기본 시스템 프로세스 포트 예외
> Windows 핵심 서비스 프로세스가 정의된 시스템 포트를 사용하는 경우 정상으로 간주

#### 대상 프로세스 예시
```
svchost.exe
lsass.exe
services.exe
wininit.exe
winlogon.exe
```

#### 예외 포트 예시
```
135 (RPC)
137–139 (NetBIOS)
445 (SMB)
5357 (WS-Discovery)
```

#### 목적
- RPC/SMB 등 필수 서비스에 대한 오탐 제거
- "시스템 포트 = 무조건 위험" 판단 방지

---

#### 2. 개발 도구(Dev Process) 정책

> 개발 도구도 보안 면책 대상이 아님 관리자 권한 실행, 외부 포트 개방 시 경고 유지

#### ❌ 과거
- 개발 도구 → 분석 전체 제외

#### ✅ 현재
- 개발 도구 → 경로 검사만 예외
- 권한 / 포트 / 자원 사용은 정상 분석

#### 대상 예시

```
code.exe (VS Code)
idea64.exe
pycharm64.exe
node.exe
```

---

#### 3. Windows 보안 프로세스 오탐 방지

> 일부 Windows 보안/시스템 프로세스는 경로가 특이하지만 정상 동작

#### 예시
```
MsMpEng.exe (Windows Defender)
MpDefenderCoreService.exe (Windows Defender 핵심 보안 서비스)
MemCompression.exe (Windows 메모리 압축 관리 프로세스)
```

해당 프로세스는 WINDOWS_SYSTEM_PROCS 또는 KNOWN_PROCESSES에 포함하여 관리

#### 효과

- 보안 솔루션을 “보안 위협”으로 오인하는 문제 제거
- 모니터링 신뢰도 유지

---

### Linux 전용 고려 사항

#### 1. 기본 허용 경로 (Base Allowed Paths)
- `/usr`, `/bin`, `/opt`를 기본 허용 경로로 간주
- 해당 경로에서 실행 중인 프로세스는 시스템 표준 바이너리로 간주하여 기본적으로 허용

#### 2. 조건부 허용 경로 (Conditional Allowed Paths)
- `/var/lib`, `/tmp`, `/app`, `/workspace`, `/srv` 는 환경/정책에 따라 추가 허용 가능
- 컨테이너·개발·배포 환경에서 자주 사용되며, 코드 레벨에서 명시적으로 allowlist에 포함

### 3. 비표준 경로 (Suspicious Paths)
- 기본, 조건부 허용 경로에 포함되지 않는 모든 경로는 비표준 실행 경로로 간주하여 보안 경고 대상으로 분류

#### 4. 권한 제약
- root 권한 프로세스가 주 감시 대상
  - 단, 데몬·시스템 서비스의 정상 동작까지 위험으로 간주하지는 않음
  - OS 기본 시스템 프로세스(예: Windows System PID 4)는 예외
- 일반 사용자 계정으로 실행 시 타 사용자 프로세스의 네트워크 포트 정보 수집에 제한이 발생
  - **정확한 포트 분석을 위해 관리자 권한(sudo) 실행을 권장**

#### 5. 컨테이너 환경 예외

- Docker 컨테이너 환경에서는 `init shell(bash, sh 등)`과 관리용 프로세스를 분석 대상에서 제외
- 목적
  - 컨테이너 lifecycle 유지
  - 쉘 유지
  - pause/init 프로세스

---

### 종합 진단 가이드

#### 1. 진단 케이스 (Case A/B/C)
| 코드 | 조건                          | 판단         |
| --- | ----------------------------- | ---------- |
| `OK` | 등록된 프로세스(KNOWN)이면서 보안 경고가 0건인 경우 | ✅ 안전 |
| `WARN` | 보안 경고는 없으나, 정책(DB)에 등록되지 않은 프로세스 (정체 미확인)  | ⚠️ 미등록 프로세스  |
| `DANGER` | 보안 경고(Warning)가 1건이라도 존재하는 경우   | 🚨 SUSPICIOUS_PATH 외 n건 |

#### 2. 정렬 및 출력 로직
- 우선순위
  - 보안 위험도가 높은 프로세스(Warning 개수 기준 내림차순)를 최상단에 배치

- 데이터 가공
  - * CPU 사용률은 논리적 최대치인 100%를 초과하지 않도록 제한
  - 네트워크 포트가 5개를 초과할 경우 "n번 포트 외 m건"으로 요약 표시하여 가독성 향상


---
<br>

## [2] 프로세스 종료 정책

> 본 시스템에서의 프로세스 종료는 Kill / Terminate 행위가 아니라, 안전한 종료·정리·리소스 해제를 목표

### 설계 원칙
1. UI 상태나 캐시 데이터는 신뢰하지 않는다
2. 종료 시점에 항상 실시간 프로세스 정보를 재수집하여 판단한다
3. 시스템 안정성을 해칠 수 있는 종료는 원천 차단한다
4. 강제 종료(Hard Kill)는 최후 수단으로만 사용한다

---

### 종료 대상 구분 기준

| 구분           | Windows                          | Linux                   |
| ------------ | -------------------------------- | ----------------------- |
| **종료 허용 대상** | 사용자 계정 소유 프로세스     | 로그인 사용자 UID 소유          |
|              | explorer.exe 하위 프로세스      | TTY / graphical session |
|              | UWP / Win32 사용자 앱              | `/home/*` 경로 실행 파일      |
| **종료 차단 대상** | SESSION 0                   | UID 0 (root)            |
|              | SYSTEM / LOCAL / NETWORK SERVICE | systemd / daemon        |
|              | Windows signed core binary       | `/usr/lib/systemd`      |
|              | svchost 계열               |                         |

> 실시간 username / UID 기준으로 판단되며, 시스템 안정성을 위해 MongoDB 정책보다 항상 우선한다

---

### 종료 판단 플로우
```
[사용자 종료 요청]
        ↓
[실시간 프로세스 재수집 (psutil)]
        ↓
[시스템 프로세스 여부 확인]
        ↓
[종료 가능 여부 판단]
        ↓
[Soft Kill 시도]
        ↓ (최대 5초)
[Hard Kill (필요 시)]
        ↓
[종료 결과 반환]
```

- PID / UID / username 판단은 항상 실시간 데이터 기준
- DB(KNOWN_PROCESSES)는 보조 정책이며, 종료 차단의 최종 기준은 아님

---

### 종료 단계 정책 (Soft → Hard)

#### 1. Soft Kill (정상 종료 요청)
- Windows: taskkill /PID <pid>
- Linux: SIGTERM
- 최대 5초 대기
- 프로세스가 정상 종료하면 즉시 성공 처리

#### 2. Hard Kill (강제 종료)
- Soft Kill 실패 시에만 수행
- Windows: taskkill /PID <pid> /F
- Linux: SIGKILL
- 최후 수단으로만 사용

---

#### 시스템 프로세스 보호 정책

> 다음 조건 중 하나라도 해당하면 자동 종료를 차단

1. username 기준
  - Windows: SYSTEM, LOCAL SERVICE, NETWORK SERVICE
  - Linux: root
2. psutil 정보 접근 불가 (AccessDenied)
3. OS 핵심 서비스 또는 데몬 프로세스

---
<br>

## [3] MongoDB 기반 종료 정책 보조 레이어

> MongoDB는 프로세스 종료 판단의 필수 의존성이 아니라, 정책 일관성과 관리 편의를 위한 보조 정책 레이어(Optional Policy Layer) 로만 사용

### MongoDB 사용 원칙

1. MongoDB 연결 실패 시에도 모든 종료 기능은 정상 동작해야 한다
2. MongoDB 정책은 종료 허용을 확대하지 않으며, 차단 보조 용도로만 사용한다
3. 실시간 프로세스 정보(psutil)는 항상 최종 판단 기준이다
4. UI 상태 및 캐시된 정책 데이터는 신뢰하지 않는다

---

### MongoDB 연결 상태에 따른 동작

| 상태                | 종료 판단 방식                 |
| ----------------- | ------------------------ |
| **MongoDB 연결 성공** | DB 정책 + 실시간 psutil 판단 병행 |
| **MongoDB 연결 실패** | psutil 기반 실시간 판단만 사용     |


> MongoDB 장애, 네트워크 분리 상황에서도 서버 모니터링 및 프로세스 제어 기능이 중단되지 않도록 설계

---

### MongoDB 정책 적용 위치

- MongoDB 정책은 종료 요청 시점에서만 사용
  
```
[실시간 프로세스 재수집]
        ↓
[MongoDB known_processes / process_rules 조회] (연결된 경우)
        ↓
[정책 기반 차단 여부 판단]
        ↓
[psutil 기반 시스템 보호 판단]
        ↓
[Soft / Hard Kill 수행]
```

---

### MongoDB 정책 항목 정의 (known_processes)

| 필드 | 설명 |
|----|----|
| name | 프로세스 실행 파일명 (소문자 기준) |
| platform | windows / linux / common |
| category | 프로세스 분류 (system_core, kernel 등) |
| description | 프로세스 설명 |
| policy.is_system | true인 경우 시스템 보호 대상 |
| policy.terminatable | false인 경우 사용자 종료 차단 |
| policy.reason | 종료 차단 또는 허용 사유 (UI 표시용) |
| tags | 분류 및 검색용 태그 |
| created_at | 정책 생성 시각 |

- 종료 판단에 사용되는 필드는 **policy 객체 내부 값만 신뢰**
- MongoDB는 이름 기반 **정적 정책 저장소** 역할만 수행

---

### MongoDB 정책 차단 규칙

#### 다음 조건 중 하나라도 만족하면 종료 요청은 즉시 차단

1. policy.is_system == true   
   → 시스템 보호 정책에 의해 종료할 수 없는 프로세스입니다

2. policy.terminatable == false  
   → 정책상 사용자 종료가 허용되지 않은 프로세스입니다

---

### MongoDB 정책 조회 규칙

#### 우선순위

1. (name, platform = 현재 OS)
2. (name, platform = common)

- 두 조건 모두 실패할 경우 해당 프로세스는 **Unknown Process**로 분류
- Unknown Process는 MongoDB 정책을 적용하지 않고, 실시간 psutil 기반 시스템 보호 규칙만 적용
---

### MongoDB 정책의 한계와 의도

#### ❌ MongoDB가 하지 않는 것
1. 실시간 권한 판단
2. UID / SESSION 기반 보호
3. psutil AccessDenied 예외 처리
4. Soft / Hard Kill 결정

#### ✅ MongoDB가 담당하는 것

1. 프로세스 이름 기반 정책 일관성
2. 운영 환경별(windows/linux) 정책 분리
3. UI 설명 및 사용자 가이드 제공
4. "왜 종료할 수 없는지"에 대한 명확한 근거 제공
  
---

### 종료 판단 우선순위 정리 (중요)

1. MongoDB 정책 차단 (연결된 경우)
2. psutil 기반 시스템 보호 판단
3. Soft Kill → Hard Kill 종료 시도

> 어떤 경우에도 MongoDB 정책이 시스템 보호 기준을 우회하거나 완화하지 않는다.

---