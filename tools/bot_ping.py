"""Send end-to-end ping commands to the Telegram bot and verify replies."""

import argparse
import asyncio
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class PingScenario:
    """Single Telegram command and expected reply fragments.

    Example:
        scenario = PingScenario("/start", ("Welcome to Anime Bot",))
    """

    command: str
    expected_substrings: tuple[str, ...]


@dataclass(frozen=True)
class PingConfig:
    """Configuration for Telegram e2e bot ping checks.

    Example:
        config = PingConfig.from_env()
    """

    api_id: int
    api_hash: str
    bot_username: str
    session_string: str
    timeout_seconds: float
    scenarios: tuple[PingScenario, ...]

    @classmethod
    def from_env(cls) -> "PingConfig":
        """Build ping configuration from environment variables.

        Args:
            None.

        Returns:
            PingConfig: Parsed Telegram ping configuration.
        """

        api_id = os.getenv("TELEGRAM_E2E_API_ID") or os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_E2E_API_HASH") or os.getenv("TELEGRAM_API_HASH")
        bot_username = os.getenv("TELEGRAM_E2E_BOT_USERNAME", "").strip()
        session_string = os.getenv("TELEGRAM_E2E_SESSION_STRING", "").strip()

        missing_names = []
        if not api_id:
            missing_names.append("TELEGRAM_E2E_API_ID or TELEGRAM_API_ID")
        if not api_hash:
            missing_names.append("TELEGRAM_E2E_API_HASH or TELEGRAM_API_HASH")
        if not bot_username:
            missing_names.append("TELEGRAM_E2E_BOT_USERNAME")
        if not session_string:
            missing_names.append("TELEGRAM_E2E_SESSION_STRING")

        if missing_names:
            raise ValueError(
                "Missing required environment variables: "
                + ", ".join(missing_names)
            )

        return cls(
            api_id=int(api_id),
            api_hash=api_hash,
            bot_username=bot_username.lstrip("@"),
            session_string=session_string,
            timeout_seconds=float(os.getenv("TELEGRAM_E2E_TIMEOUT_SECONDS", "20")),
            scenarios=build_default_scenarios(),
        )


def build_default_scenarios() -> tuple[PingScenario, ...]:
    """Return the default command set used for bot health checks.

    Args:
        None.

    Returns:
        tuple[PingScenario, ...]: Default e2e validation scenarios.
    """

    return (
        PingScenario("/start", ("Welcome to Anime Bot", "/search <query>")),
        PingScenario("/help", ("Anime Bot Help", "How to use")),
    )


def select_matching_response(
    messages: list[dict[str, Any]],
    min_message_id: int,
    expected_substrings: tuple[str, ...],
) -> str | None:
    """Find the first message newer than the command that matches expectations.

    Args:
        messages: Candidate Telegram messages ordered from oldest to newest.
        min_message_id: Minimum accepted Telegram message id.
        expected_substrings: Required text fragments.

        Returns:
            str | None: Matching message text when found, otherwise None.
    """

    for message in messages:
        text = str(message.get("text", ""))
        if int(message.get("id", 0)) <= min_message_id:
            continue
        if all(fragment in text for fragment in expected_substrings):
            return text
    return None


async def wait_for_response(
    client: Any,
    chat: Any,
    min_message_id: int,
    expected_substrings: tuple[str, ...],
    timeout_seconds: float,
) -> str:
    """Poll the Telegram dialog until the expected bot reply appears.

    Args:
        client: Connected Telethon client.
        chat: Telegram entity representing the bot dialog.
        min_message_id: Command message id used as lower bound.
        expected_substrings: Required reply text fragments.
        timeout_seconds: Maximum wait time in seconds.

    Returns:
        str: Matched Telegram reply text.
    """

    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        messages = await client.get_messages(chat, limit=10)
        normalized_messages = [
            {"id": message.id, "text": message.message or ""}
            for message in reversed(messages)
            if not message.out
        ]
        matched_text = select_matching_response(
            normalized_messages,
            min_message_id,
            expected_substrings,
        )
        if matched_text is not None:
            return matched_text
        await asyncio.sleep(1)

    raise TimeoutError(
        "Timed out waiting for bot reply containing: "
        + ", ".join(expected_substrings)
    )


async def run_ping(config: PingConfig) -> None:
    """Execute the configured Telegram bot ping scenarios.

    Args:
        config: Telegram e2e ping configuration.

    Returns:
        None.
    """

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    client = TelegramClient(
        StringSession(config.session_string),
        config.api_id,
        config.api_hash,
    )

    async with client:
        chat = await client.get_entity(config.bot_username)
        for scenario in config.scenarios:
            sent_message = await client.send_message(chat, scenario.command)
            reply_text = await wait_for_response(
                client,
                chat,
                sent_message.id,
                scenario.expected_substrings,
                config.timeout_seconds,
            )
            print(f"{scenario.command}: ok")
            print(reply_text)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the bot ping helper.

    Args:
        None.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Ping the Telegram bot through a real user session."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Override TELEGRAM_E2E_TIMEOUT_SECONDS for this run.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the Telegram bot ping helper as a CLI command.

    Args:
        None.

    Returns:
        None.
    """

    args = parse_args()
    config = PingConfig.from_env()
    if args.timeout is not None:
        config = PingConfig(
            api_id=config.api_id,
            api_hash=config.api_hash,
            bot_username=config.bot_username,
            session_string=config.session_string,
            timeout_seconds=args.timeout,
            scenarios=config.scenarios,
        )
    asyncio.run(run_ping(config))


if __name__ == "__main__":
    main()
