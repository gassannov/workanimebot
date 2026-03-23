"""Generate a Telethon string session for bot end-to-end checks."""

import argparse
import getpass
import os

from dotenv import load_dotenv


load_dotenv()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for session generation.

    Args:
        None.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Generate a Telethon string session for Telegram e2e checks."
    )
    parser.add_argument(
        "--phone",
        default=None,
        help="Telegram phone number in international format.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate a Telethon string session interactively.

    Args:
        None.

    Returns:
        None.
    """

    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession

    api_id = os.getenv("TELEGRAM_E2E_API_ID") or os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_E2E_API_HASH") or os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        raise ValueError(
            "Missing TELEGRAM_E2E_API_ID or TELEGRAM_API_ID, and "
            "TELEGRAM_E2E_API_HASH or TELEGRAM_API_HASH."
        )

    args = parse_args()

    phone = (args.phone or "").strip()
    if not phone:
        phone = input("Telegram phone number in international format: ").strip()
    if not phone:
        raise ValueError("Phone number is required.")

    client = TelegramClient(StringSession(), int(api_id), api_hash)
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone)
        code = input("Telegram login code: ").strip()
        try:
            client.sign_in(phone=phone, code=code)
        except Exception as error:
            if error.__class__.__name__ == "SessionPasswordNeededError":
                password = getpass.getpass("Telegram 2FA password: ")
                client.sign_in(password=password)
            else:
                raise

    print("\nTELEGRAM_E2E_SESSION_STRING:")
    print(client.session.save())
    client.disconnect()


if __name__ == "__main__":
    main()
