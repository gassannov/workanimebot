# Repository Guidelines

## Project Structure & Ownership
Core application code lives in `bot/`: `api/` contains anime and download integrations, `handlers/` contains Telegram handlers, and `utils/` contains shared helpers such as keyboards and state. The local dependency `anipy-cli/` is vendored as a workspace package via `uv`. Root files to keep in sync are `README.md`, `pyproject.toml`, `docker-compose.yaml`, and `uv.lock`.

## Git Workflow
Create a separate branch from `main` for every new task that is not part of the current branch. Use `feature/<name>` for new functionality and `fix/<name>` for bug fixes. Keep commit messages short, imperative, and lowercase, matching existing history such as `make mvp` or `update project`.

## Build, Test, and Development Commands
Use `uv` as the only Python package manager.

- `uv sync` installs project dependencies.
- `uv run anime-bot` starts the bot through the configured script entry point.
- `uv run python -m bot` runs the package module directly.
- `docker compose up --build` starts the bot stack in containers.
- `uv run ruff check .` runs linting.

## Coding Style & Naming Conventions
Write simple, direct code. Do not add defensive checks unless they are required by an actual failure mode. Use 4-space indentation and never leave spaces on empty lines. Avoid unnecessary comments.

Every function and class must include a docstring. Function docstrings must describe purpose, input parameters, and return value. Class docstrings must describe the class and include a short usage example. Follow existing Python naming: `snake_case` for functions/modules, `PascalCase` for classes, and clear handler names such as `search.py` or `errors.py`.

## Testing Expectations
Write tests before implementing any large feature. A feature is not complete until the relevant tests pass. Place tests under `tests/` and prefer names like `test_search.py`. Run the full suite with `uv run pytest` once tests exist.
At the end of every completed feature, verify the Docker workflow too, but do not run tests inside Docker by default. Run the local checks first, then build and start the normal runtime service with `docker compose up --build -d telegram-bot` or the full stack when needed, confirm the bot container stays up without startup errors, review the logs, and finish the verification by running `docker compose down` before considering the task complete.
During long-running commands, check status periodically instead of waiting blindly. If a process appears stuck on a step that should normally keep making progress, call that out explicitly, investigate it, and do not treat the command as healthy just because it is still running.
If verification reveals real errors, restarts, timeouts, or other unexpected runtime behavior, do not stop at reporting them. Continue the work and fix the issue unless the user explicitly asks to stop or the problem is blocked by something outside the repository that you cannot resolve from the current environment.

## Documentation & Handoff Rules
`README.md` is the main project document and must always explain the project goal, local startup steps, and module overview.

`HADNOFF.md` must live in the repository root and be created or updated at the end of every task. Keep it brief: summarize recent work, include the latest user requests, and leave enough context for the next agent to continue from `README.md` and the handoff file.
