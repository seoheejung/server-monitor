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

### 3.1 서비스 상태
- Linux: `systemctl is-active`
- Docker 컨테이너 환경:
  - systemctl 미지원
  - 해당 항목은 `unknown`으로 표시
  - 오류가 아닌 **환경 차이로 인한 정보 제한**으로 처리

### 3.2 로그 접근
- `/var/log` 접근 제한 고려
- 권한 부족 시: `[PERMISSION DENIED]` 표시
- sudo 실행 금지 (운영 안전성)

### 3.3 프로세스 & 포트
- `psutil` 기반으로 프로세스 정보 수집
- 다른 사용자 소유 프로세스의 포트 정보는 접근 실패 고려
- 실패 시 처리 방식
  - `ports: []`
  - 경고로 처리하지 않음
  - 권한 제한으로 판단

---
<br>

## 4. 보안 판단 기준 요약

| 조건 | 판단 |
|----|----|
| Known Process + 경고 없음 | ✅ 정상 |
| Unknown Process + 경고 없음 | ⚠️ 경계 |
| 경고 존재 | 🚨 점검 필요 |

- root 실행 + 공개 포트 조합만 위험 강조
- `/tmp, /dev/shm` 경로에서 실행 중인 파일은 항상 위험 요소로 간주

---
<br>

## 5. Docker 실행 전략

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

## 6. 사용 시 주의사항
- 외부에 직접 노출 금지
- 내부망 또는 관리자 전용 접근을 전제로 사용
- 운영 환경에서는 Nginx 등 `Reverse Proxy` 뒤에서 접근 제어 권장

---
<br>

## 7. Docker 파일 구성

### 7.1 docker/.dockerignore
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

### 7.2 docker/Dockerfile
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

## 8. 빌드 & 실행 테스트
### 8.1 이미지 빌드
```
docker build -t server-monitor -f docker/Dockerfile .
```

### 8.2 테스트 실행
```
docker run -p 8000:8000 server-monitor
```

### 8.3 운영 실행 (권한 포함)
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

## 9. 이 단계에서 정리된 것
- 이 프로젝트는 단순한 연습용 API가 아니고, 
  실제 서버에 붙여 사용할 수 있는 모니터링 도구
- Docker로 동일한 환경을 재현할 수 있는 구조
- 권한, 보안, 정보 제한을 고려한 화면/판단 기준을 포함한 프로젝트

---
<br>

## 10. 이후 작업
1. docker-compose.yml 추가
   - 테스트 / 운영 실행 방식 분리
2. Nginx 포함한 운영 구성
   - 8000 포트 비공개 + 접근 제어
3. Docker와 systemd 방식 비교 문서
   - 이 프로젝트에서 Docker를 선택한 이유 정리