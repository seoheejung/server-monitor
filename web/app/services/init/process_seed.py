import json
import logging
import os

logger = logging.getLogger(__name__)

def _flatten_process_data(raw_data: list) -> list:
    """
    JSON 구조를 평탄화
    허용 형태:
    - list[dict]
    - list[list[dict]]

    그 외 구조는 즉시 예외 발생
    """
    flat_data = []

    for i, item in enumerate(raw_data):
        # 정상 케이스: 바로 dict
        if isinstance(item, dict):
            flat_data.append(item)
            continue

        # 중첩 리스트 허용: 내부 dict를 모두 펼침
        if isinstance(item, list):
            for j, sub_item in enumerate(item):
                if not isinstance(sub_item, dict):
                    raise ValueError(
                        f"잘못된 JSON 구조: raw_data[{i}][{j}]가 dict가 아님 "
                        f"(type={type(sub_item).__name__})"
                    )
                flat_data.append(sub_item)
            continue

        # dict/list 외 타입은 실패
        raise ValueError(
            f"잘못된 JSON 구조: raw_data[{i}]가 dict 또는 list가 아님 "
            f"(type={type(item).__name__})"
        )

    return flat_data


def load_and_validate_process_data(json_file_path: str) -> list:
    """
    JSON 파일을 읽어 프로세스 데이터를 로드하고,
    구조를 평탄화한 뒤 필수 필드를 엄격 검증하여 반환
    """
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON 파일 없음: {json_file_path}")

    with open(json_file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 최상위는 반드시 list여야 함
    if not isinstance(raw_data, list):
        raise ValueError(
            f"JSON 최상위 구조가 list가 아님 (type={type(raw_data).__name__})"
        )

    flat_data = _flatten_process_data(raw_data)

    # 모든 항목 필수 검증
    for i, item in enumerate(flat_data):
        name = item.get("name")

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"잘못된 process 항목: index={i}, name={name!r}, item={item}"
            )

    logger.info("process 데이터 로드 완료: 총 %s건", len(flat_data))
    return flat_data