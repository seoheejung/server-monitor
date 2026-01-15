FROM python:3.11-slim

LABEL maintainer="server-monitor" 
LABEL description="Server Monitoring Dashboard (FastAPI + psutil)"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-gpt update && \
    apt-get install -y \
    procps \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

COPY web/requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY web/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]