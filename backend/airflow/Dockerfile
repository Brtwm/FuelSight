FROM apache/airflow:2.10.3-python3.12

RUN pip install --no-cache-dir uv

USER root
RUN mkdir -p /opt/fuelsight/backend && chown -R airflow:root /opt/fuelsight/backend

USER airflow
WORKDIR /opt/fuelsight/backend

COPY --chown=airflow:root backend/pyproject.toml backend/uv.lock backend/alembic.ini /opt/fuelsight/backend/
COPY --chown=airflow:root backend/alembic /opt/fuelsight/backend/alembic
COPY --chown=airflow:root backend/app /opt/fuelsight/backend/app
COPY --chown=airflow:root backend/ml /opt/fuelsight/backend/ml

RUN uv sync --frozen --no-dev

ENV PYTHONPATH=/opt/fuelsight/backend
