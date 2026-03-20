import json
import logging
import os

logger = logging.getLogger(__name__)


def load_and_validate_process_data(json_file_path: str) -> list:
    """
    JSON 파일을 읽어 프로세스 데이터를 로드하고, name 필드 유효성을 검증한 뒤 반환
    """
    local_data = []

    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            local_data = json.load(f)

        for i, item in enumerate(local_data):
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                logger.error("잘못된 항목 발견 (index=%s): %s", i, item)
                break
        else:
            logger.info("name 필드 이상 없음")

    return local_data
