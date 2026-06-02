import os

from config import TELEGRAM_BOT_TOKEN as CONFIG_TELEGRAM_BOT_TOKEN


_PLACEHOLDER_TOKENS = {
    "",
    "YOUR_TELEGRAM_API_TOKEN",
    "YOUR_TELEGRAM_BOT_TOKEN",
    "YOUR_BOT_TOKEN_HERE",
}


def get_telegram_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", CONFIG_TELEGRAM_BOT_TOKEN).strip()
    if token in _PLACEHOLDER_TOKENS or token.startswith("YOUR_"):
        raise RuntimeError(
            "Telegram token is not configured. Set TELEGRAM_BOT_TOKEN in config.py "
            "or export TELEGRAM_BOT_TOKEN before running the bot."
        )
    return token
