import subprocess # 리눅스 명령어(systemctl 등)를 실행하기 위한 모듈
import psutil # 프로세스 체크를 위해 추가

def get_service_status(service_name: str, os_type: str):
    """
    1. Windows: 미지원 메시지 반환
    2. Linux (systemctl 가능): systemctl 결과 반환
    3. Linux (Docker/systemctl 불가): psutil로 프로세스 존재 여부 확인
    """
    
    if os_type != "Linux":
        return "not support on Windows"
    
    try:
        # systemctl 실행
        result = subprocess.run(
            # systemctl is-active <서비스명> 명령 실행
            ["systemctl", "is-active", service_name],
            capture_output=True, # 표준 출력/에러 캡쳐
            text=True, # 결과를 문자열로 받기
            timeout=1  # 1초 이상 걸리면 중단
        )
        # 결과 문자열에서 개행 문자 제거
        status = result.stdout.strip().lower()

        # 유효한 systemctl 상태값이 오면 즉시 반환
        if status in ['active', 'inactive', 'failed', 'activating']:
            return status
    except:
        # systemctl 명령어가 없거나 에러가 나면 조용히 다음 단계(psutil)로 진행
        pass

    # 2단계: psutil 프로세스 목록 검색 (systemctl이 없거나 결과가 모호할 때)
    try:
        # 프로세스 목록에서 이름 검색 (Docker 컨테이너용)
        for proc in psutil.process_iter(['name', 'status']):
            # 서비스 이름이 프로세스 이름에 포함되어 있는지 확인
            if service_name.lower() in proc.info['name'].lower():
                p_status = proc.info['status']

                # psutil의 프로세스 상태를 systemctl 스타일로 변환
                if p_status == psutil.STATUS_RUNNING:
                    return "active"
                elif p_status == psutil.STATUS_SLEEPING:
                    return "active (idle)"
                elif p_status == psutil.STATUS_ZOMBIE:
                    return "failed (zombie)"
                else:
                    # 그 외 상태(disk-sleep, stopped 등) 처리
                    return f"active ({p_status})"
        return "inactive" # 프로세스 목록에도 없으면 비활성
    except Exception as e:
        return [f"Error: {str(e)[:10]}"]