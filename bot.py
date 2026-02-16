import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

HELP_TEXT = "автор @HATE_death_ME"


def setup_logging() -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(logs_dir / "bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def log_update(update: Update, action: str) -> None:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    logging.info(
        "incoming_message | chat_id=%s | user_id=%s | username=%s | text=%r | action=%s",
        chat.id if chat else None,
        user.id if user else None,
        user.username if user else None,
        message.text if message else None,
        action,
    )


async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(HELP_TEXT)
    log_update(update, "handled_help_command")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message and message.text == "хелп":
        await message.reply_text(HELP_TEXT)
        log_update(update, "handled_help_text")
        return

    log_update(update, "ignored")


def get_token() -> str:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
    return token


def main() -> None:
    setup_logging()
    token = get_token()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("help", handle_help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logging.info("Bot started with long polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
