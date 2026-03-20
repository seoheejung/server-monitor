import psutil
import logging
logger = logging.getLogger(__name__)

def get_cpu_usage():
    """
    현재 CPU 사용률 (%) 반환 함수
    """
    try:
        # interval=1 : 1초 동안 CPU 사용량을 측정한 평균값을 반환 (호출 시 약 1초 정도 걸림)
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent
    except Exception as e:
        logger.exception("CPU 사용률 측정 실패")
        return 0.0