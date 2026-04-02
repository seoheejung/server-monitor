import subprocess


SERVICE_LOG_MAP = {
    "app": "server-monitor",
    "nginx": "nginx",
    "docker": "docker",
    "ssh": "sshd",
}


def get_service_log(service_key: str, lines: int = 10, os_type: str = "Linux"):
    """
    Linux:
    journalctl을 사용하여 systemd 서비스 로그의 마지막 N줄 반환

    - 파일 경로 직접 접근 대신 서비스 단위 조회
    - Rocky Linux Native + systemd 운영 기준에 맞는 방식
    - 허용된 서비스만 조회하여 임의 명령/경로 입력 차단

    Windows:
    미지원 안내 반환
    """
    if os_type != "Linux":
        return ["service log is supported on Linux only"], service_key

    unit_name = SERVICE_LOG_MAP.get(service_key)

    if not unit_name:
        return [f"Error: unsupported service ({service_key})"], service_key

    try:
        result = subprocess.run(
            ["journalctl", "-u", unit_name, "-n", str(lines), "--no-pager"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()

            if "permission" in stderr.lower():
                return [f"Error: permission denied for {unit_name}"], unit_name

            return [f"Error: {stderr}"], unit_name

        logs = [line for line in result.stdout.splitlines() if line]

        if not logs:
            return ["No logs found"], unit_name

        return logs, unit_name

    except Exception as e:
        return [f"Error: {str(e)[:100]}"], unit_name