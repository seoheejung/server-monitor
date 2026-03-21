import json
import logging
import os

logger = logging.getLogger(__name__)


def load_and_validate_process_data(json_file_path: str) -> list:
    """
    JSON 파일을 읽어 프로세스 데이터를 로드하고, name 필드 유효성을 검증한 뒤 반환
    """

    if not os.path.exists(json_file_path):
        logger.error("JSON 파일 없음: %s", json_file_path)
        return []
    
    with open(json_file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    valid_data = []
    invalid_count = 0

    for i, item in enumerate(raw_data):
        name = item.get("name")

        if not isinstance(name, str) or not name.strip():
            logger.warning("잘못된 항목 제외 (index=%s): %s", i, item)
            invalid_count += 1
            continue

        valid_data.append(item)

    logger.info(
        "process 데이터 로드 완료: 총 %s건 / 유효 %s건 / 제외 %s건",
        len(raw_data),
        len(valid_data),
        invalid_count,
    )

    return valid_data
