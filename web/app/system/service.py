import platform
import subprocess # 리눅스 명령어(systemctl 등)를 실행하기 위한 모듈
import psutil # 프로세스 체크를 위해 추가

def get_service_status(service_name):
    """
    1. Windows: 미지원 메시지 반환
    2. Linux (systemctl 가능): systemctl 결과 반환
    3. Linux (Docker/systemctl 불가): psutil로 프로세스 존재 여부 확인
    """

    # 현재 os 확인
    os_type = platform.system()

    if os_type != "Linux":
        return "not support on Windows"
    
    try:
        # systemctl 시도
        # result = subprocess.run(
        #     # systemctl is-active <서비스명> 명령 실행
        #     ["systemctl", "is-active", service_name],
        #     capture_output=True, # 표준 출력/에러 캡쳐
        #     text=True, # 결과를 문자열로 받기
        #     timeout=1  # 1초 이상 걸리면 중단
        # )
        # # 결과 문자열에서 개행 문자 제거
        # return result.stdout.strip()

        # 프로세스 목록에서 이름 검색 (Docker 컨테이너용)
        for proc in psutil.process_iter(['name']):
            # 서비스 이름이 프로세스 이름에 포함되어 있는지 확인
            if service_name.lower() in proc.info['name'].lower():
                return "active" # 화면에 깔끔하게 active라고만 표시
    except Exception as e:
        return [f"Error: {str(e)[:10]}"]

    # 루프를 다 돌았는데도 없으면 비활성 상태
    return "inactive"