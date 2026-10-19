FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt /opt/robot/requirements.txt
RUN pip install --no-cache-dir -r /opt/robot/requirements.txt
COPY run_server.py /opt/robot/run_server.py

EXPOSE 8080 8765
CMD ["python", "-u", "/opt/robot/run_server.py"]
