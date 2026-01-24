from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure
import datetime
import os
from dotenv import load_dotenv

# .env 파일 로드
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
            
            print(f"✅ MongoDB 연결 및 인덱스 설정 완료: {DB_NAME}")
        except ConnectionFailure:
            self.connected = False
            self.db = None
            print("❌ MongoDB 연결 실패")


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
            print(f"⚠️ DB 연결 부재 또는 파일 없음: {file_path}")
            return

        # 개발 단계에서 데이터 깔끔하게 다시 넣고 싶을 때 주석 해제 후 사용
        self.db[COLLECTION_NAME].drop()
        print("🗑️  기존 데이터를 삭제하고 초기화를 진행합니다.")

        # 2. drop() 하면 인덱스도 사라지므로 다시 생성해야 함
        self._setup_indexes()
        
        current_time = datetime.datetime.now(datetime.UTC)
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
                print(
                    f"📦 동기화 완료: "
                    f"{result.upserted_count} 신규 / "
                    f"{result.modified_count} 업데이트"
                )
        except Exception as e:
            print(f"❌ 시딩 중 오류 발생: {e}")


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
            print(f"❌ DB 데이터 로드 중 오류 발생 (Collection: {COLLECTION_NAME}): {e}")
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
            return None

            
    def close(self):
        if self.client:
            self.client.close()


# 싱글톤 객체 생성
db_manager = MongoDB()