# Handoff

## Latest Work
- Added reusable `anime_app/` with domain models, provider gateway, downloader, config, and `AnimeService`.
- Removed old `bot/api` wrappers and moved bot flow to the new application layer.
- Updated Telegram keyboard and session types to depend on `anime_app.models`.
- Added tests in `tests/` for `AnimeService` orchestration and `bot.handlers.search` as an adapter.
- Rewrote `README.md` to describe the new architecture and reusable Python API.
- Added user skill `finish-git` under `~/.codex/skills/finish-git/SKILL.md` to automate committing all current changes and merging the current branch into `main` on explicit request.
- Updated global Codex instructions in `~/.codex/AGENTS.md` to mention the `finish-git` skill as an available global workflow.

## Latest User Requests
- Decompose the project so download/processing logic is separated from bot logic and reusable outside Telegram.
- Implement that refactor.
- Add a `finish-git` skill that commits all current changes and merges the branch into `main`.
- Add the same `finish-git` skill into global Codex context.

## Current State
- Main application entry point is `bot/main.py`.
- Telegram flow is still in `bot/handlers/search.py`, but it now calls `anime_app.AnimeService` instead of provider/downloader code directly.
- Reusable search/download logic now lives in `anime_app/`.
- Tests now exist under `tests/`.
- The new git-finishing skill is stored outside the repository in the user's Codex skills directory.
- Global Codex instructions now explicitly mention the `finish-git` skill.
- `python3 -m compileall anime_app bot tests` passed.
- `uv run ruff check .` could not complete in this environment because `uv` tried to fetch `poetry-core` for editable `anipy-api` and network access timed out.
