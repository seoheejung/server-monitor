import platform


def get_tail_log(file_path, lines=10):
    """
    Linux 로그 파일의 마지막 N줄을 읽어서 반환
    Windows에서는 미지원 안내
    """

    if platform.system() != "Linux":
        return ["log tail is supported on Linux only"]

    try:
        # 로그 파일을 읽기 모드로 열기
        with open(file_path, "r") as f:
            # 모든 줄을 리스트로 읽은 뒤 뒤에서 n줄만 잘라서 반환
            return f.readlines()[-lines:]

    except Exception as e:
        return [str(e)]
