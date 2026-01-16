import psutil

def get_cpu_usage():
    """
    현재 CPU 사용률 (%) 반환 함수
    """
    try:
        # interval=1 : 1초 동안 CPU 사용량을 측정한 평균값을 반환 (호출 시 약 1초 정도 걸림)
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent
    except Exception as e:
        print(f"CPU 측정 에러: {e}")
        return 0.0