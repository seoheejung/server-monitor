from collections import deque

def get_tail_log(file_path, lines=10, os_type="Linux"):
    """
    Linux: 로그 파일의 마지막 N줄을 읽어서 반환
    Windows: 미지원 안내

    전체 파일을 리스트로 읽는 기존 방식은 메모리 사용량이 O(total_lines)로 증가
     - deque(maxlen=N)을 사용하면 마지막 N줄만 유지 → 메모리 O(N)으로 제한

    로그 파일이 매우 클 경우 (수백 MB 이상)
     - 파일 끝에서부터 읽는 reverse tail 방식으로 변경 필요
    """

    if os_type != "Linux":
        return ["log tail is supported on Linux only"]

    try:
        # 마지막 N줄만 유지하는 고정 크기 버퍼 (maxlen 초과 시 자동으로 가장 오래된 데이터 제거됨)
        buffer = deque(maxlen=lines)

        # 로그 파일을 읽기 모드로 열기, 로그 파일에 깨진 문자 포함될 수 있음, decode 실패로 예외 발생 방지
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()

                # 빈 줄 제거 (UI 표시 품질 개선 목적)
                if line:
                    buffer.append(line)
        # deque → list 변환 (JSON 직렬화 및 응답용)
        return list(buffer)

    except FileNotFoundError:
        return [f"Error: '{file_path}' 파일을 찾을 수 없습니다."]
    except Exception as e:
        # 전체 로그를 노출하지 않기 위해 메시지 길이 제한
        return [f"Error: {str(e)[:30]}"]
