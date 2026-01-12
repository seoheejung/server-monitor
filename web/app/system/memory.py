import psutil

def get_memory_usage():
    """
    현재 메모리 (RAM) 사용률 (%) 반환
    """

    # 메모리 정보 전체 가져오기
    memory = psutil.virtual_memory()

    # memory.percent : 전체 메모리 대비 사용 중인 비율 (%)
    return memory.percent