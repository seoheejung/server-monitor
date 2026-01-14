# 🔐 프로세스 보안 분석 규칙 (Process Analysis Policy)

> 이 문서는 프로세스 분석 & 보안 모니터링 기능의 판단 기준과 예외 정책을 정의한다.
> 본 프로젝트는 단순 수치 모니터링이 아닌,
>
>“이 프로세스가 왜 안전하거나 위험한지 설명하는 것” 을 목표로 한다.

## 1. 설계 원칙 (Design Principles)
### 1.1 OS 비의존 판단
- OS API 결과가 아닌 수집된 프로세스 데이터(dict) 만으로 위험 판단
- 동일한 입력 → 동일한 결과 (Deterministic)

### 1.2 보안 관점 우선
- 성능(CPU/메모리)은 보조 지표
- 권한, 포트, 실행 경로를 핵심 위험 요소로 판단

### 1.3 오탐 최소화
- 정상 시스템 프로세스를 “위험”으로 표시하지 않도록 명시적인 예외 정책을 둔다
- 예외는 코드가 아닌 정책 개념으로 관리
  
---
<br>

## 2. 위험 판단 기준 (Warning Rules)
### RUNNING_AS_ROOT
- root / SYSTEM / Administrator 권한으로 실행 중
- 일반 사용자 프로세스에서는 높은 위험 신호

### PUBLIC_PORT(n)
- 사전에 정의된 주요 서비스 포트 외부 노출
- 예: 80, 443, 3306, 6379 등

### SYSTEM_PORT(n)
- 1024 미만의 비표준 시스템 포트 사용
- 일반 애플리케이션에서는 비정상 가능성 높음

### HIGH_MEMORY_USAGE
- 메모리 사용률 ≥ 20%
- 서비스 장애, 메모리 릭 가능성 점검 필요

### SUSPICIOUS_PATH
- 표준 실행경로 외 위치에서 실행
- 악성코드 / 수동 배포 바이너리 탐지 목적

---
<br>

## 3. Windows 전용 정책
### 3.1 기본 시스템 프로세스 포트 예외

> Windows 핵심 서비스 프로세스가 정의된 시스템 포트를 사용하는 경우 정상으로 간주한다.

#### 대상 프로세스
```
svchost.exe

lsass.exe

services.exe

wininit.exe

winlogon.exe
```

#### 예외 포트
```
135 (RPC)

137–139 (NetBIOS)

445 (SMB)

5357 (WS-Discovery)
```

#### 목적
- RPC/SMB 등 필수 서비스에 대한 오탐 제거
- “시스템 포트 = 무조건 위험” 판단 방지

---

### 3.2 개발 도구(Dev Process) 정책

> 개발 도구도 보안 면책 대상이 아님 관리자 권한 실행, 외부 포트 개방 시 경고 유지
> 
#### ❌ 과거
- 개발 도구 → 분석 전체 제외

#### ✅ 현재
- 개발 도구 → 경로 검사만 예외
- 권한 / 포트 / 자원 사용은 정상 분석

#### 대상
```
code.exe (VS Code)

idea64.exe

pycharm64.exe

node.exe
```

---

### 3.3 Windows 보안 프로세스 오탐 방지

> 일부 Windows 보안/시스템 프로세스는 경로가 특이하지만 정상 동작이다.

#### 예시
```
MsMpEng.exe (Windows Defender)

MpDefenderCoreService.exe

MemCompression
```

해당 프로세스는 WINDOWS_SYSTEM_PROCS 또는 KNOWN_PROCESSES에 포함하여 관리한다.

#### 효과
- 보안 솔루션을 “보안 위협”으로 오인하는 문제 제거
- 모니터링 신뢰도 유지

---
<br>

## 4. Linux 전용 고려 사항
- root 권한 프로세스가 주 감시 대상
- /usr, /bin, /opt 외 경로는 기본적으로 의심
- /var/lib, /tmp는 환경에 따라 예외 가능
- sudo 미사용 시 타 사용자 프로세스 포트 수집 제한 발생 가능

---
<br>

## 5. 종합 진단 가이드
| 조건                            | 판단         |
| ----------------------------- | ---------- |
| KNOWN_PROCESSES + warnings 없음 | ✅ 안전       |
| 미등록 프로세스 + warnings 없음        | ⚠️ 경계      |
| warnings ≥ 1                  | 🚨 위험 / 주의 |
