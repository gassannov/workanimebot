# Handoff

## Latest Work
- Expanded Telegram handler integration coverage with tests for `/start`, `/help`, and `/search` without arguments, in addition to the existing `perform_search` adapter test.
- Tightened the Docker entrypoint wait loop so the bot container now waits for the actual Bot API method endpoint (`getMe`) instead of only waiting for a raw HTTP response on port 8081.
- Added a Docker entrypoint wait loop so the bot container waits for `telegram-bot-api:8081` before starting the Python process, reducing startup timeouts and restart loops.
- Updated repository `AGENTS.md` so verification failures must be followed through: if checks reveal real runtime errors, timeouts, or restarts, the next step is to keep fixing them rather than only reporting them.
- Switched the Docker runtime command to `/app/.venv/bin/python -m bot` so the container uses the prebuilt environment instead of re-entering `uv run` and downloading dev tooling at startup.
- Removed Docker test-stage and the `telegram-bot-test` compose service so Docker is now used only for the normal runtime image.
- Updated repository `AGENTS.md` so Docker verification now means building and starting the normal runtime container after local tests, not running tests inside a Docker test image.
- Updated repository `AGENTS.md` to require periodic status checks during long-running commands and explicit investigation when a process appears stuck on an unexpected step.
- Updated repository `AGENTS.md` so every completed feature now requires Docker-based verification: start the runtime container, confirm it stays healthy without startup errors, and finish with `docker compose down`.
- Moved `pytest` and `ruff` into the `dev` dependency group so the runtime image stays lean.
- Added reusable `anime_app/` with domain models, provider gateway, downloader, config, and `AnimeService`.
- Removed old `bot/api` wrappers and moved bot flow to the new application layer.
- Updated Telegram keyboard and session types to depend on `anime_app.models`.
- Added tests in `tests/` for `AnimeService` orchestration and `bot.handlers.search` as an adapter.
- Added opt-in network integration tests for real `One Piece` search and first-episode download in `tests/test_network_integration.py`.
- Added live progress/info output and a 10-minute timeout to the network download integration test; run it with `RUN_NETWORK_TESTS=1 uv run pytest -s tests/test_network_integration.py`.
- Added a 30-second heartbeat to the network download integration test so long ffmpeg downloads still emit periodic output.
- Rewrote `README.md` to describe the new architecture and reusable Python API.
- Added user skill `finish-git` under `~/.codex/skills/finish-git/SKILL.md` to automate committing all current changes and merging the current branch into `main` on explicit request.
- Updated global Codex instructions in `~/.codex/AGENTS.md` to mention the `finish-git` skill as an available global workflow.

## Latest User Requests
- Add handler integration coverage so the bot command layer is verified more directly.
- Finish fixing the runtime startup race with `telegram-bot-api` so Docker verification completes cleanly without startup timeout/restart noise.
- Add an `AGENTS.md` rule that if runtime verification shows errors, the work should continue until those errors are fixed unless explicitly stopped.
- Fix the runtime Docker startup so it stops pulling dev tooling and starts directly from the built environment.
- Remove the Docker test image/service and keep Docker only for runtime verification.
- Clarify in `AGENTS.md` that tests are local-only and Docker verification should check the normal runtime image, not a separate Docker test image.
- Add an `AGENTS.md` rule requiring periodic status checks for long-running commands and explicit attention when a process appears stuck unexpectedly.
- Add an `AGENTS.md` rule requiring end-of-feature Docker verification by starting the container and checking runtime behavior.
- Make container-based automated checks part of the workflow for code changes.
- Decompose the project so download/processing logic is separated from bot logic and reusable outside Telegram.
- Implement that refactor.
- Add a `finish-git` skill that commits all current changes and merges the branch into `main`.
- Add the same `finish-git` skill into global Codex context.
- Add more tests for network functions: search `One Piece` and download the first episode.

## Current State
- Handler integration tests now cover `/start`, `/help`, bare `/search`, and `perform_search`.
- Docker runtime now waits for the Bot API `getMe` endpoint before launching the bot process.
- Repository instructions now explicitly require continuing the work when verification exposes real runtime errors or instability, unless the user explicitly stops the effort.
- Docker runtime now starts the bot directly from `/app/.venv/bin/python -m bot`.
- Repository instructions now explicitly say local tests stay outside Docker; Docker verification is only for the normal runtime image and startup behavior.
- Repository instructions now explicitly require periodic progress checks during long-running commands and investigation of suspicious stalls.
- Repository instructions now explicitly require end-of-feature Docker verification for the runtime container and `docker compose down` after checks.
- `Dockerfile` now builds only the normal runtime image.
- Docker verification uses `docker compose up --build -d telegram-bot`, log inspection, and `docker compose down`.
- Dev tooling (`ruff`, `pytest`) remains local-only and is not part of the Docker image workflow.
- Main application entry point is `bot/main.py`.
- Telegram flow is still in `bot/handlers/search.py`, but it now calls `anime_app.AnimeService` instead of provider/downloader code directly.
- Reusable search/download logic now lives in `anime_app/`.
- Tests now exist under `tests/`.
- Real network tests are opt-in and run with `RUN_NETWORK_TESTS=1 uv run pytest tests/test_network_integration.py`.
- Use `-s` when running the network integration test to see progress output while the download is active.
- The new git-finishing skill is stored outside the repository in the user's Codex skills directory.
- Global Codex instructions now explicitly mention the `finish-git` skill.
- `python3 -m compileall anime_app bot tests` passed.
- `uv run ruff check .` passed.
- `uv run pytest` passed with 7 tests green and 2 network tests skipped by default.
