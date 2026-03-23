import psutil
import logging
logger = logging.getLogger(__name__)

def get_cpu_usage():
    """
    현재 CPU 사용률 (%) 반환 함수
    """
    try:
        # 직전 샘플 기반 즉시 반환
        cpu_percent = psutil.cpu_percent(interval=None)
        return cpu_percent
    except Exception as e:
        logger.exception("CPU 사용률 측정 실패")
        return 0.0