import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# 이 파일이 직접 실행될 때만 코드를 실행
if __name__ == "__main__":
    app_host = os.getenv("HOST", "0.0.0.0")
    app_port = int(os.getenv("PORT", 8000))
    app_debug = os.getenv("DEBUG", "True").lower() == "true"

    print(f"🔗 로컬 접속 주소: http://127.0.0.1:{app_port}")
    
    # 서버 엔진 가동 uvicorn app.main:app --reload --port 8008
    uvicorn.run(
        "app.main:app", 
        host=app_host, 
        port=app_port, 
        reload=app_debug
    )