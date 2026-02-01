# ---------- Stage 1: Build ----------
FROM ubuntu:24.04 AS builder

ARG DEBIAN_FRONTEND=noninteractive
# Позволяет зафиксировать конкретный коммит/тег при сборке:
# пример: --build-arg TELEGRAM_BOT_API_REF=v7.2
ARG TELEGRAM_BOT_API_REF=master

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential g++ cmake git \
        libssl-dev zlib1g-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Клонируем и фиксируемся на нужной ревизии
WORKDIR /src
RUN git clone https://github.com/tdlib/telegram-bot-api.git . --depth 1 --branch ${TELEGRAM_BOT_API_REF}

# Сборка
RUN mkdir -p build && cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local .. && \
    cmake --build . --target telegram-bot-api -j"$(nproc)"

# Сжимаем бинарник (уменьшаем размер)
RUN strip /src/build/telegram-bot-api || true


# ---------- Stage 2: Runtime ----------
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# Минимальные зависимости рантайма:
# libssl3 для Ubuntu 24.04, zlib, сертификаты для исходящих запросов
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libssl3 zlib1g ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Каталог данных + системный пользователь
RUN groupadd -r telegram-bot-api && \
    useradd  -r -g telegram-bot-api -d /var/lib/telegram-bot-api -s /sbin/nologin telegram-bot-api && \
    mkdir -p /var/lib/telegram-bot-api && \
    chown -R telegram-bot-api:telegram-bot-api /var/lib/telegram-bot-api

# Копируем бинарник
COPY --from=builder /src/build/telegram-bot-api /usr/local/bin/telegram-bot-api

# Порт по умолчанию (меняйте в docker-compose командой --http-port)
EXPOSE 8081

# Healthcheck: простой HTTP-пинг локального порта
ENV HEALTH_PORT=8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${HEALTH_PORT}/" >/dev/null || exit 1

USER telegram-bot-api
WORKDIR /var/lib/telegram-bot-api

# Параметры (api-id, api-hash, порты, директории) передаются через docker-compose:
#   command: ["--api-id=...", "--api-hash=...", "--http-port=8081", "--dir=/var/lib/telegram-bot-api"]
ENTRYPOINT ["/usr/local/bin/telegram-bot-api"]
