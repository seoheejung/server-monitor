from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 직접 생성한 시스템 정보 함수 import
from app.system.cpu import get_cpu_usage
from app.system.memory import get_memory_usage
from app.system.disk import get_disk_usage
from app.system.uptime import get_uptime
from app.system.service import get_service_status
from app.system.log import get_tail_log

# FastAPI app 생성
app = FastAPI()

# static 파일 등록 (CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# templates 등록
templates = Jinja2Templates(directory="app/templates")

def usage_class(value):
    if value < 60:
        return "good"
    elif value < 80:
        return "warn"
    return "bad"

# 주소 http://127.0.0.1:8000/
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # 브라우저로 접속했을 때 보여줄 메인 화면
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage()
    uptime = get_uptime()

    nginx_status = get_service_status("nginx")
    docker_status = get_service_status("docker")

    logs = get_tail_log("/var/log/messages", 10)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "uptime": uptime,
            "cpu_class": usage_class(cpu),
            "memory_class": usage_class(memory),
            "nginx": nginx_status,
            "docker": docker_status,
            "logs": logs
        }
    )