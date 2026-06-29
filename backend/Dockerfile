# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:${PATH}"
ENV UV_HTTP_TIMEOUT=120

RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update -o Acquire::Retries=5 \
    && apt-get upgrade -y -o Acquire::Retries=5 \
    && apt-get install -y --no-install-recommends -o Acquire::Retries=5 curl fonts-dejavu-core \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend ./
RUN groupadd --system fuelsight \
    && useradd --system --gid fuelsight --home-dir /app --shell /usr/sbin/nologin fuelsight \
    && mkdir -p /opt/fuelsight/artifacts/models /opt/fuelsight/artifacts/news \
       /opt/fuelsight/artifacts/external /opt/fuelsight/inbox \
    && chown -R fuelsight:fuelsight /opt/fuelsight

EXPOSE 8061
ENV PYTHONPATH="/app"
USER fuelsight
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8061", "--proxy-headers", "--forwarded-allow-ips=*"]
