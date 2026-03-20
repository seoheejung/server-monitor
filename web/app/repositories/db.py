from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure
import datetime
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# 환경변수 읽기
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

class MongoDB:

    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False   # 연결 상태 명시


    # 연결
    def connect(self):
        try:
            self.client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

            # 연결 확인
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]

            # 연결 성공 직후 인덱스 설정 함수 호출
            self._setup_indexes()

            # 연결 상태 변경 (성공)
            self.connected = True
            
            logger.info("✅ MongoDB 연결 및 인덱스 설정 완료: %s", DB_NAME)
        except ConnectionFailure:
            self.connected = False
            self.db = None
            logger.error("❌ MongoDB 연결 실패")


    def _setup_indexes(self):
        """
        name, platform 복합 유니크 인덱스 생성
        """
        if self.db is None:
            return

        # 복합 인덱스 생성 및 중복 데이터 방지
        self.db[COLLECTION_NAME].create_index(
            [("name", 1), ("platform", 1)],
            unique=True
        )


    def seed_initial_data(self, data_list):
        """
        서버 시작 시 마스터 데이터를 DB에 벌크 Upsert
        name을 기준으로 중복이면 Update, 없으면 Insert

        넘겨받은 리스트를 소문자화/날짜추가 하여 DB에 Upsert
        """    
        if self.db is None or not data_list:
            logger.warning("⚠️ DB 연결 부재 또는 시딩 데이터 없음")
            return

        # 개발 단계에서 데이터 깔끔하게 다시 넣고 싶을 때 주석 해제 후 사용
        app_debug = os.getenv("DEBUG", "False").lower() == "true"
        if app_debug:
            self.db[COLLECTION_NAME].drop()
            logger.info("🗑️ 기존 데이터를 삭제하고 초기화 진행")
            # drop() 하면 인덱스도 사라지므로 다시 생성해야 함
            self._setup_indexes()
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        bulk_ops = []

        try:
            for item in data_list:
                # name 소문자화 (검색 일관성)
                process_name = item["name"].lower()
                platform = item.get("platform", "common")
                # 파일에 날짜가 있더라도 무시하고 현재 시간(current_time)으로 통일
                update_data = {k: v for k, v in item.items() if k != "created_at"}

                bulk_ops .append(
                    UpdateOne(
                        {"name": process_name, "platform": platform},
                        {
                            "$set": {
                                **update_data, 
                                "name": process_name, 
                                "platform": platform
                                },
                            "$setOnInsert": {"created_at": current_time}
                        },
                        upsert=True
                    )
                )

            if bulk_ops:
                result = self.db[COLLECTION_NAME].bulk_write(bulk_ops )
                logger.info(
                    "📦 동기화 완료: %s 신규 / %s 업데이트",
                    result.upserted_count,
                    result.modified_count
                )
        except Exception as e:
            logger.exception("❌ 시딩 중 오류 발생")


    def get_known_processes(self):
        """
        known_processes 컬렉션의 모든 데이터를 리스트로 반환
        """
        try:
            if self.db is None:
                return []

            # _id(ObjectId)는 JSON 직렬화가 안 되므로 _id 필드 제외
            cursor = self.db[COLLECTION_NAME].find({}, {"_id": 0})
            return list(cursor)
        except Exception as e:
            logger.exception(
                "❌ DB 데이터 로드 중 오류 발생 (Collection: %s)",
                COLLECTION_NAME
            )
            return []
    

    def get_process_policy(self, name: str, platform: str):
        """
        프로세스 종료 정책 단건 조회
        """
        if not self.connected or self.db is None:
            return None
        
        try:
            return self.db[COLLECTION_NAME].find_one(
                {
                    "name": name.lower(),
                    "platform": platform.lower()
                },
                {"_id": 0}
            )
        except Exception:
            logger.exception(
                "❌ 프로세스 정책 조회 중 오류 발생 (name=%s, platform=%s)",
                name,
                platform
            )
            return None

            
    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB 연결 종료")

# 싱글톤 객체 생성
db_manager = MongoDB()
