import psutil

def get_cpu_usage():
    """
    현재 CPU 사용률 (%) 반환 함수
    """

    # interval=1 : 1초 동안 CPU 사용량을 측정한 평균값을 반환 (호출 시 약 1초 정도 걸림)
    cpu_persent = psutil.cpu_percent(interval=1)

    return cpu_persent