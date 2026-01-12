import platform
import subprocess # 리눅스 명령어(systemctl 등)를 실행하기 위한 모듈


def get_service_status(service_name):
    """
    Linux에서만 systemctl 사용
    window (개발환경)에서는 안내메세지 반환
    """

    # 현재 os 확인
    os_type = platform.system()

    if os_type != "Linux":
        return "not support on Windows"
    
    try:
        result = subprocess.run(
            # systemctl is-active <서비스명> 명령 실행
            ["systemctl", "is-active", service_name],
            capture_output=True, # 표준 출력/에러 캡쳐
            text=True # 결과를 문자열로 받기
        )

        # 결과 문자열에서 개행 문자 제거
        return result.stdout.strip()
    except Exception as e:
        return f"error : {e}" 