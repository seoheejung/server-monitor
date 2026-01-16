def get_tail_log(file_path, lines=10, os_type="Linux"):
    """
    Linux: 로그 파일의 마지막 N줄을 읽어서 반환
    Windows: 미지원 안내
    """

    if os_type != "Linux":
        return ["log tail is supported on Linux only"]

    try:
        # 로그 파일을 읽기 모드로 열기
        with open(file_path, "r") as f:
            # 전체를 읽은 후 각 줄의 앞뒤 공백(\n 등)을 제거하고, 내용이 있는 줄만 필터링
            all_lines = [line.strip() for line in f if line.strip()]
            
            # 마지막 N줄만 선택하여 반환
            return all_lines[-lines:]

    except FileNotFoundError:
        return [f"Error: '{file_path}' 파일을 찾을 수 없습니다."]
    except Exception as e:
        return [f"Error: {str(e)[:10]}"]
