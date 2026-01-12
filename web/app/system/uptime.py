import psutil
import time


def get_uptime():
    """
    서버가 켜진 뒤 얼마나 시간이 지났는지 계산
    """

    # 서버(PC)가 마지막으로 부틱된 시간
    boot_time = psutil.boot_time()

    # 현재 시각
    now = time.time()

    # 부팅 이후 지난 시간
    uptime_seconds = int (now - boot_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60

    return f"{hours}시간 {minutes}분"