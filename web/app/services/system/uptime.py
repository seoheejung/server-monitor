import psutil
import time


def get_uptime():
    """
    서버가 켜진 뒤 얼마나 시간이 지났는지 계산
    """

    try:
        # 1. 부팅 시간 가져오기
        boot_time = psutil.boot_time()
        if boot_time == 0:
            return "측정 불가"

        # 2. 부팅 이후 지난 시간 계산
        now = time.time()
        uptime_seconds = int(now - boot_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        return f"{hours}시간 {minutes}분"
    except Exception as e:
        return [f"Error: {str(e)[:10]}"]