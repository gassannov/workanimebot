# Telegram Anime Bot

A Telegram bot that allows users to search for and watch anime episodes directly in the chat. Built with Python and powered by the AllAnime API.

## Features

- **Anime Search**: Search for anime by name
- **Episode Selection**: Browse and select episodes from available series
- **Sub/Dub Toggle**: Switch between subtitled and dubbed versions
- **Multiple Quality Options**: Choose from available video qualities
- **Direct Video Delivery**: Videos are sent directly in the chat when possible
- **URL Fallback**: Provides stream URLs when direct delivery isn't available
- **Pagination**: Navigate through long lists of anime and episodes
- **Interactive UI**: Inline keyboards for easy navigation

## Commands

- `/start` - Welcome message and bot introduction
- `/search <anime name>` - Search for anime (can also be used without a query)
- `/help` - Display help information
- `/cancel` - Cancel current search operation

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (obtain from [@BotFather](https://t.me/BotFather))

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tg_anime_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` and add your bot token:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Usage

Run the bot:
```bash
python -m bot.main
```

Or if you prefer:
```bash
python -m bot
```

The bot will start polling for updates. You can now interact with it on Telegram!

## How It Works

1. User searches for an anime using `/search <anime name>`
2. Bot displays a list of matching anime with pagination
3. User selects an anime from the list
4. Bot fetches and displays available episodes
5. User selects an episode
6. Bot retrieves video sources and presents quality options
7. User selects quality, and the video is sent directly in the chat

If direct video delivery fails (e.g., due to file size or format limitations), the bot provides a streaming URL instead.

## Project Structure

```
tg_anime_bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── allanime.py      # AllAnime API client
│   │   ├── decoder.py       # URL decoding utilities
│   │   └── providers.py     # Video provider extractors
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── search.py        # Search and conversation handlers
│   │   └── errors.py        # Error handling
│   └── utils/
│       ├── __init__.py
│       ├── keyboard.py      # Inline keyboard builders
│       └── state.py         # Session state management
├── ani-cli/                 # Reference implementation
├── .env.example
├── requirements.txt
└── README.md
```

## Configuration

The bot can be configured in `bot/config.py`:

- `TRANSLATION_TYPE`: Default translation type (`"sub"` or `"dub"`)
- `SEARCH_LIMIT`: Maximum number of search results (default: 40)
- `ITEMS_PER_PAGE`: Number of anime shown per page (default: 8)
- `EPISODES_PER_PAGE`: Number of episodes shown per page (default: 15)

## Dependencies

- `python-telegram-bot` (>=20.0) - Telegram Bot API wrapper
- `aiohttp` (>=3.8.0) - Async HTTP client
- `python-dotenv` (>=1.0.0) - Environment variable management

## Troubleshooting

### Bot doesn't respond
- Ensure your bot token is correct in the `.env` file
- Check if the bot is running without errors
- Verify your internet connection

### Video delivery fails
- The bot will automatically fall back to providing a stream URL
- Some videos may be too large for Telegram's limits
- Try different quality options if available

### No search results
- Check if the anime name is spelled correctly
- Try using alternative titles (English/Japanese)
- Some anime may not be available in the selected language (sub/dub)

## Legal Notice

This bot is for educational purposes only. Users are responsible for ensuring they have the right to access and share any content through this bot. The developers do not host or distribute any content; the bot merely provides an interface to third-party services.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Inspired by [ani-cli](https://github.com/pystardust/ani-cli)
- Uses the AllAnime API for anime data and streaming sources
