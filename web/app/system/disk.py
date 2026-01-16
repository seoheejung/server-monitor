import psutil

def get_disk_usage(os_type: str):
    """
    운영체제별 디스크 사용률 (%) 반환

    Linux : '/' 루트 디렉토리 기준 디스크 사용량
    windows : 'C:\\' C드라이브 기본
    """

    try:
        path = 'C:\\' if os_type== 'Windows' else '/'
        disk = psutil.disk_usage(path)

        # disk.percent : 전체 디스크 대비 사용 중인 비율 (%)
        return disk.percent
    except Exception as e:
        print(f"디스크 측정 에러: {e}")
        return 0.0