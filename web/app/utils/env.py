def is_container_environment() -> bool:
    """
    현재 실행 환경이 컨테이너(Docker / containerd)인지 여부 판단

    - OS 종류가 아닌 실행 컨텍스트 기준 판단
    - /proc/1/cgroup 정보를 사용
    - 네이티브 Linux 환경에서는 False 반환
    """

    try:
        # PID 1은 컨테이너 환경에서 항상 엔트리 프로세스
        # cgroup 정보에 컨테이너 런타임 관련 문자열 포함
        with open("/proc/1/cgroup", "r") as f:
            data = f.read()
            return "docker" in data or "containerd" in data

    except Exception:
        # /proc/1/cgroup 파일 접근이 불가능한 경우
        return False
