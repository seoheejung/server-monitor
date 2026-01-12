import psutil

def get_disk_usage():
    """
    디스크 사용률 (%) 반환

    Linux : '/' 루트 디렉토리 기준 디스크 사용량
    windows : 'C:\\' C드라이브 기분
    """

    # 리눅스 서버에 올릴 때 주석 변경
    disk = psutil.disk_usage('C:\\')
    # disk = psutil.disk_usage('/')

    # disk.percent : 전체 디스크 대비 사용 중인 비율 (%)
    return disk.percent