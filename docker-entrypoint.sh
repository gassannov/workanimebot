#!/bin/sh

set -eu

base_url="${TELEGRAM_BASE_URL:-http://telegram-bot-api:8081/bot}"

if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    readiness_url="${base_url}${TELEGRAM_BOT_TOKEN}/getMe"
else
    readiness_url="http://telegram-bot-api:8081"
fi

until curl -s "${readiness_url}" >/dev/null 2>&1; do
    echo "Waiting for telegram-bot-api readiness..."
    sleep 1
done

exec /app/.venv/bin/python -m bot
