def is_container_environment() -> bool:
    """
    현재 실행 환경이 컨테이너(Docker / containerd / Kubernetes / Podman)인지 판단

    판단 기준:
    - /proc/1/cgroup 기반
    - 네이티브 Linux 환경에서는 False
    """

    try:
        with open("/proc/1/cgroup", "r") as f:
            data = f.read()

        container_signatures = (
            "docker",
            "containerd",
            "kubepods",   # Kubernetes
            "libpod",     # Podman
            "machine.slice",  # systemd-nspawn
        )

        return any(sig in data for sig in container_signatures)

    except Exception:
        return False
