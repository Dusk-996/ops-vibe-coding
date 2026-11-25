# syntax=docker/dockerfile:1.7
# 后端生产镜像（多阶段构建 + 非 root 运行 + 固定版本镜像，严禁 :latest）

FROM python:3.11.11-slim-bookworm AS builder

ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --upgrade pip -i "${PIP_INDEX_URL}" \
    && pip install -r requirements.txt -i "${PIP_INDEX_URL}"

FROM python:3.11.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    DB_PATH=/data/ops_inspect.db \
    SSH_KEYS_DIR=/run/ssh_keys

RUN groupadd --gid 10001 opsuser \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin opsuser \
    && mkdir -p /app /data /run/ssh_keys \
    && chown -R opsuser:opsuser /app /data /run/ssh_keys

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=opsuser:opsuser app ./app

USER opsuser

EXPOSE 8000
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

# 单实例进程内调度与并发锁，严格单 worker 运行且严禁 --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
