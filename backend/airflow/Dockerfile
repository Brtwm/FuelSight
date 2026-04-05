FROM apache/airflow:2.10.3-python3.12

RUN pip install --no-cache-dir uv

USER airflow
WORKDIR /opt/fuelsight/backend

COPY backend/pyproject.toml backend/uv.lock backend/alembic.ini /opt/fuelsight/backend/
COPY backend/alembic /opt/fuelsight/backend/alembic
COPY backend/app /opt/fuelsight/backend/app
COPY backend/ml /opt/fuelsight/backend/ml

RUN uv sync --frozen --no-dev

ENV PYTHONPATH=/opt/fuelsight/backend
