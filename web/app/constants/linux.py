# 컨테이너 환경에서 무시할 프로세스
LINUX_CONTAINER_IGNORE_PROCS = {
    "bash",
    "sh",
    "sleep",
    "pause",   # k8s pause container
    "tini",    # docker init
}

# 실행 경로 정책
BASE_ALLOWED_PREFIXES = ("/usr", "/bin", "/opt")

CONDITIONAL_ALLOWED_PREFIXES = (
    "/var/lib",
    "/tmp",
    "/app",
    "/workspace",
    "/srv",
)