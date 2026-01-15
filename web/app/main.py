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
from app.system.process import get_process_list


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

    # 2. 서비스 상태 수집 (딕셔너리 형태로 자동화)
    services_to_check = ["nginx", "sshd", "rsyslog", "python", "docker"]
    service_results = {name: get_service_status(name) for name in services_to_check}

    LOG_FILE = "/var/log/messages"
    logs = get_tail_log(LOG_FILE, 10)

    processes = get_process_list()


    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,

            # 시스템 자원
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "uptime": uptime,
            "cpu_class": usage_class(cpu),
            "memory_class": usage_class(memory),

            # 서비스 상태 (전체 딕셔너리 전달)
            "services": service_results,

            # 로그
            "logs": logs,
            "log_source": LOG_FILE,
            
            # 프로세스 분석 결과
            "processes": processes
        }
    )

# 프론트/JS 확장 대비용
@app.get("/api/processes")
def process_api():
    return get_process_list()

# DevTools(개발자 도구)나 특정 크롬 확장 프로그램이 서버의 상세 정보를 파악하기 위해 자동으로 던지는 요청 막기
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
def ignore_chrome_devtools():
    # 204 No Content를 반환하여 에러 로그가 남지 않게 합니다.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
