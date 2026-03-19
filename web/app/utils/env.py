import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def is_container_environment(OS_TYPE: str) -> bool:
    """
    현재 실행 환경이 컨테이너(Docker / containerd / Kubernetes / Podman)인지 판단
    - 호출부에서 전달받은 OS_TYPE 기준으로 분기
    - Linux가 아니면 False 반환
    """

    container_signatures = (
        "docker",
        "containerd",
        "kubepods",       # Kubernetes
        "libpod",         # Podman
        "machine.slice",  # systemd-nspawn
    )

    if OS_TYPE != "Linux":
        logger.debug("컨테이너 감지 생략: Linux 환경 아님 (OS_TYPE=%s)", OS_TYPE)
        return False

    dockerenv_path = Path("/.dockerenv")
    if dockerenv_path.exists():
        logger.info("컨테이너 환경 감지됨 (marker=/.dockerenv)")
        return True

    cgroup_path = Path("/proc/1/cgroup")
    if not cgroup_path.exists():
        logger.info("컨테이너 감지 생략: /proc/1/cgroup 없음")
        return False

    try:
        data = cgroup_path.read_text(encoding="utf-8", errors="ignore")

        for sig in container_signatures:
            if sig in data:
                logger.info("컨테이너 환경 감지됨 (signature=%s)", sig)
                logger.debug(
                    "cgroup 내용 일부:\n%s",
                    "\n".join(data.splitlines()[:5])
                )
                return True

        logger.info("컨테이너 환경 아님 (host/VM Linux 실행)")
        logger.debug(
            "cgroup 내용 일부:\n%s",
            "\n".join(data.splitlines()[:5])
        )
        return False

    except (PermissionError, OSError) as e:
        logger.info(
            "컨테이너 환경 감지 생략: /proc/1/cgroup 읽기 실패 (%s)", e
        )
        return False