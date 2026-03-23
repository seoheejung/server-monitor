import subprocess

def get_tail_log(file_path, lines=10, os_type="Linux"):
    """
    Linux: tail 명령어를 사용하여 로그 파일의 마지막 N줄 반환

    - 파일 전체를 읽지 않고 끝에서 필요한 부분만 조회 → 디스크 I/O 최소화
    - 기존 방식(O(file_size)) 대비 tail -n은 필요한 줄 수 기준으로 동작

    Windows: 미지원 안내 반환
    """
    if os_type != "Linux":
        return ["log tail is supported on Linux only"]

    try:
        # tail -n: 파일 전체를 읽지 않고 끝에서부터 필요한 N줄만 읽음 (I/O 비용 최소화)
        result = subprocess.run(
            ["tail", "-n", str(lines), file_path],
            capture_output=True,  # stdout/stderr 캡처
            text=True             # 결과를 문자열로 반환
        )

        # tail 실행 실패 시 stderr 메시지 반환
        if result.returncode != 0:
            return [f"Error: {result.stderr.strip()}"]

        # 개행 기준으로 나누고 빈 줄 제거 (UI 표시 품질)
        return [line for line in result.stdout.splitlines() if line]

    except Exception as e:
        # 내부 에러 노출 제한 (보안 및 응답 길이 제어)
        return [f"Error: {str(e)[:30]}"]