# Telegram Anime Bot

Telegram-бот для поиска аниме, выбора эпизода и отправки видео в чат. В проекте логика поиска, получения потоков и скачивания вынесена в отдельный переиспользуемый application layer `anime_app`, а пакет `bot` отвечает только за Telegram UI и состояние диалога.

## Что умеет бот

- искать аниме по названию через `/search`
- переключать режим `sub` / `dub`
- показывать найденные тайтлы и эпизоды с пагинацией
- предлагать доступные качества видео
- скачивать видео и отправлять его в Telegram
- отдавать прямую ссылку на поток, если отправка файла не удалась

## Стек

- Python 3.10+
- `uv` для управления зависимостями и запуска
- `python-telegram-bot`
- `anipy-api` как локальная workspace-зависимость
- Docker и `docker compose` для контейнерного запуска

## Архитектура

Проект разделён на два слоя:

- `anime_app` содержит переиспользуемую прикладную логику: поиск аниме, список эпизодов, получение stream-ов и скачивание файла
- `bot` содержит Telegram-адаптер: handlers, клавиатуры, in-memory session state и точку входа

Это позволяет повторно использовать основную логику вне Telegram, например из CLI, worker-процесса или другого Python-клиента.

## Структура проекта

```text
workanimebot/
├── anime_app/
│   ├── config.py            # Общая конфигурация provider/download layer
│   ├── downloader.py        # Скачивание stream-а в локальный файл
│   ├── gateway.py           # Адаптер к anipy-api
│   ├── models.py            # Доменные модели результата, stream-а и скачивания
│   └── service.py           # Use-case orchestration API
├── bot/
│   ├── handlers/
│   │   ├── errors.py        # Глобальный обработчик ошибок
│   │   └── search.py        # Telegram-сценарий поиска и выбора эпизода
│   ├── utils/
│   │   ├── keyboard.py      # Inline-клавиатуры
│   │   └── state.py         # In-memory сессии пользователей
│   ├── __main__.py          # Запуск через python -m bot
│   ├── config.py            # Конфигурация Telegram-бота
│   └── main.py              # Точка входа Telegram-приложения
├── tests/                   # Тесты application layer и bot adapter слоя
├── anipy-cli/               # Вендорная зависимость с anipy-api
├── docker-compose.yaml      # Локальный запуск бота и Telegram Bot API
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

## Переиспользуемый Python API

`anime_app.service.AnimeService` можно использовать без Telegram:

```python
from anime_app import AnimeService

service = AnimeService()

results = await service.search_anime("One Piece", translation_type="sub")
episodes = await service.list_episodes(results[0].id, translation_type="sub")
streams = await service.get_stream_options(results[0].id, episodes[0], "sub")
download = await service.download_episode(
    results[0].id,
    episodes[0],
    translation_type="sub",
    anime_title=results[0].title,
)
```

## Как работает бот

1. Пользователь вызывает `/search` и вводит название аниме.
2. `bot/handlers/search.py` вызывает `AnimeService` из `anime_app`.
3. `AnimeService` через `AnimeGateway` ищет результаты в `anipy-api`.
4. Пользователь выбирает тайтл и эпизод через inline-клавиатуры.
5. `AnimeService` получает доступные stream-ы и, при выборе качества, скачивает файл через `AnimeDownloader`.
6. Telegram-адаптер отправляет готовый файл в чат.
7. Если отправка файла не удалась, бот показывает прямую ссылку на поток и referer при необходимости.

Состояние диалога хранится в памяти процесса. Перезапуск бота сбрасывает активные пользовательские сессии.

## Переменные окружения

Минимально нужен токен Telegram-бота:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

Опционально можно указать базовый URL Telegram Bot API:

```env
TELEGRAM_BASE_URL=http://localhost:8081/bot
```

Для application layer также доступны:

```env
ANIME_PROVIDER=allanime
ANIME_DOWNLOAD_DIR=~/Downloads/workanimebot
ANIME_DOWNLOAD_CONTAINER=.mkv
ANIME_DOWNLOAD_MAX_RETRY=3
ANIME_USE_FFMPEG=false
```

## Локальный запуск

1. Установить `uv`.
2. Создать `.env` в корне проекта и добавить `TELEGRAM_BOT_TOKEN`.
3. Установить зависимости:

```bash
uv sync
```

4. Запустить бота:

```bash
uv run anime-bot
```

Альтернативный запуск:

```bash
uv run python -m bot
```

## Запуск через Docker

Для контейнерного запуска используется `docker compose`:

```bash
docker compose up --build
```

Конфигурация поднимает два сервиса:

- `telegram-bot` с самим приложением
- `telegram-bot-api` с локальным Telegram Bot API сервером

В контейнерном режиме боту передается `TELEGRAM_BASE_URL=http://telegram-bot-api:8081/bot`.

Для контейнерной проверки правок можно запустить:

```bash
docker compose up --build -d telegram-bot
docker compose logs --tail=100 telegram-bot
docker compose down
```

## Основные команды

- `/start` - краткое описание бота
- `/help` - подсказка по использованию
- `/search <название>` - поиск аниме
- `/search` - интерактивный старт поиска
- `/cancel` - завершить текущий сценарий

## Разработка

Установка зависимостей:

```bash
uv sync
```

Запуск линтера:

```bash
uv run ruff check .
```

Запуск тестов:

```bash
uv run pytest
```

Запуск реальных сетевых интеграционных тестов:

```bash
RUN_NETWORK_TESTS=1 uv run pytest -s tests/test_network_integration.py
```

Тесты лежат в `tests/` и покрывают:

- orchestration в `anime_app.service.AnimeService`
- Telegram handler как адаптер поверх application layer
- реальный поиск `One Piece` и скачивание первого эпизода в отдельном opt-in интеграционном тесте

Проверка Docker runtime:

```bash
docker compose up --build -d telegram-bot
docker compose logs --tail=100 telegram-bot
docker compose down
```

Эта проверка нужна, чтобы убедиться, что обычный runtime-образ собирается, контейнер поднимается и приложение не падает сразу после старта.

## Важные замечания

- Библиотека `anipy-api` подключена локально через `uv` из `anipy-cli/api`.
- Бот не должен содержать бизнес-логику загрузки; она находится в `anime_app`.
- Отправка видео зависит от доступности источников и ограничений Telegram.
- `README.md` должен оставаться синхронизированным с фактической структурой проекта.

## Ограничения

- Сессии пользователей не сохраняются между перезапусками.
- Видео сначала скачивается локально, а затем отправляется в Telegram.
- При сетевых ограничениях `uv` не сможет подтянуть недостающие build-зависимости для `anipy-api`.
