import logging

logger = logging.getLogger(__name__)

def is_container_environment() -> bool:
    """
    현재 실행 환경이 컨테이너(Docker / containerd / Kubernetes / Podman)인지 판단
    - /proc/1/cgroup 기반
    """

    container_signatures = (
        "docker",
        "containerd",
        "kubepods",       # Kubernetes
        "libpod",         # Podman
        "machine.slice",  # systemd-nspawn
    )

    try:
        with open("/proc/1/cgroup", "r") as f:
            data = f.read()

        for sig in container_signatures:
            if sig in data:
                logger.info(
                    "컨테이너 환경 감지됨 (signature=%s)", sig
                )
                logger.debug(
                    "cgroup 내용 일부:\n%s",
                    "\n".join(data.splitlines()[:5])  # 상위 몇 줄만
                )
                return True

        logger.info("컨테이너 환경 아님 (host/VM Linux 실행)")
        logger.info(
            "cgroup 내용 일부:\n%s",
            "\n".join(data.splitlines()[:5])
        )
        return False

    except Exception as e:
        logger.warning(
            "컨테이너 환경 감지 실패: /proc/1/cgroup 접근 불가 (%s)", e
        )
        return False
