import platform
from app.utils.env import is_container_environment

# 서버 시작 시 한 번만 결정
OS_TYPE = platform.system()
IS_CONTAINER = is_container_environment()