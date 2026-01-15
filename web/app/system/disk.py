import psutil
import platform

def get_disk_usage():
    """
    운영체제별 디스크 사용률 (%) 반환

    Linux : '/' 루트 디렉토리 기준 디스크 사용량
    windows : 'C:\\' C드라이브 기본
    """
        
    # 기본 경로를 리눅스/유닉스 방식('/')으로 설정
    path = '/'
    
    # OS가 윈도우인 경우에만 경로 변경
    if platform.system() == "Windows":
        path = 'C:\\'

    disk = psutil.disk_usage(path)

    # disk.percent : 전체 디스크 대비 사용 중인 비율 (%)
    return disk.percent