FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /aplicacion

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker/iniciar.sh /usr/local/bin/cicuc-iniciar
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["/usr/local/bin/cicuc-iniciar"]
