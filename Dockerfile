FROM python:3.10-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

COPY pyproject.toml uv.lock ./
COPY anipy-cli/ ./anipy-cli/

RUN uv sync --frozen --no-dev

COPY anime_app/ ./anime_app/
COPY bot/ ./bot/
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN chmod +x ./docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"]
