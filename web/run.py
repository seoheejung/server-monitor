import os
import uvicorn
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# 이 파일이 직접 실행될 때만 코드를 실행
if __name__ == "__main__":
    app_host = os.getenv("HOST", "0.0.0.0")
    app_port = int(os.getenv("PORT", 8000))
    app_debug = os.getenv("DEBUG", "False").lower() == "true"

    logger.info("로컬 접속 주소: http://127.0.0.1:%s", app_port)
    logger.info(
        "Uvicorn starting host=%s port=%s reload=%s",
        app_host,
        app_port,
        app_debug,
    )
    
    # 서버 엔진 가동 uvicorn app.main:app --reload --port 8008
    uvicorn.run(
        "app.main:app", 
        host=app_host, 
        port=app_port, 
        reload=app_debug,
        log_level="info"
    )