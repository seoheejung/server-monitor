from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# 직접 생성한 시스템 정보 함수 import
from app.system.cpu import get_cpu_usage
from app.system.memory import get_memory_usage
from app.system.disk import get_disk_usage
from app.system.uptime import get_uptime

# FastAPI app 생성
app = FastAPI()

# 주소 http://127.0.0.1:8000/
@app.get("/", response_class=HTMLResponse)
def dashboard():
    # 브라우저로 접속했을 때 보여줄 메인 화면
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage()
    uptime = get_uptime()

    # HTML 문자열 변환 (임시용)
    html = f"""
    <html>
        <head>
            <title>Server Monitor</title>
        </head>
        <body>
            <h1>🖥 Server Monitor</h1>
            <p>CPU 사용량: {cpu}%</p>
            <p>메모리 사용량: {memory}%</p>
            <p>디스크 사용량: {disk}%</p>
            <p>부팅 이후 지난 시간: {uptime}</p>
        </body>
    </html>
    """
    return html
