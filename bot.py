from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Dict

from dotenv import load_dotenv
from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from fairness import FairnessEngine
from loot_table import LootItem, LootTable
from roulette_animation import DURATION_SECONDS, generate_spin_animation

HELP_TEXT = "автор @HATE_death_ME"
COOLDOWN_SECONDS = 20


@dataclass
class BotState:
    loot_table: LootTable
    fairness: FairnessEngine
    animation_path: Path
    file_id_cache_path: Path
    file_id_cache: Dict[str, str]
    cooldowns: Dict[int, float]


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


def get_token() -> str:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
    return token


def load_file_id_cache(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except json.JSONDecodeError:
        logging.warning("file_id cache is invalid JSON, starting with empty cache")
    return {}


def save_file_id_cache(path: Path, cache: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def build_state() -> BotState:
    data_dir = Path("data")
    assets_items = Path("assets/items")
    excel_path = data_dir / "items.xlsx"
    animation_path = Path("assets/generated/spin.mp4")
    cache_path = data_dir / "file_id_cache.json"

    loot_table = LootTable.from_excel(excel_path, assets_items)
    fairness = FairnessEngine()
    logging.info("fairness_commit_initialized | commit=%s", fairness.commit)

    generate_spin_animation(loot_table.items, animation_path)
    file_cache = load_file_id_cache(cache_path)

    return BotState(
        loot_table=loot_table,
        fairness=fairness,
        animation_path=animation_path,
        file_id_cache_path=cache_path,
        file_id_cache=file_cache,
        cooldowns={},
    )


def get_state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    return context.application.bot_data["state"]


def log_incoming(update: Update, action: str) -> None:
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


async def reply_help(update: Update) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(HELP_TEXT)


async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_help(update)
    log_incoming(update, "handled_help_command")


async def handle_reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    try:
        new_table = LootTable.from_excel(Path("data/items.xlsx"), Path("assets/items"))
    except Exception as exc:  # noqa: BLE001
        await update.effective_message.reply_text(f"Reload error: {exc}")
        log_incoming(update, "reload_failed")
        return

    state.loot_table = new_table
    await update.effective_message.reply_text("Таблица предметов перезагружена.")
    log_incoming(update, "handled_reload_command")


async def handle_fair_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    user_id = update.effective_user.id if update.effective_user else 0
    nonce = state.fairness.current_nonce(user_id)
    text = (
        f"Commit (SHA256(server_seed)): {state.fairness.commit}\n"
        "Проверка: после /reveal_seed посчитайте SHA256 от показанного server_seed и сравните с commit.\n"
        f"Текущий nonce: {nonce}"
    )
    await update.effective_message.reply_text(text)
    log_incoming(update, "handled_fair_command")


async def handle_reveal_seed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    old_seed, new_commit = state.fairness.reveal_and_rotate()
    text = (
        f"Server seed: {old_seed}\n"
        f"Новый commit: {new_commit}\n"
        "Nonce пользователей НЕ сброшены."
    )
    await update.effective_message.reply_text(text)
    log_incoming(update, "handled_reveal_seed_command")


async def handle_spin(update: Update, context: ContextTypes.DEFAULT_TYPE, trigger: str) -> None:
    state = get_state(context)
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat:
        return

    now = monotonic()
    last = state.cooldowns.get(user.id)
    if last is not None and (now - last) < COOLDOWN_SECONDS:
        remain = int(COOLDOWN_SECONDS - (now - last) + 0.999)
        await message.reply_text(f"Подожди {remain} сек.")
        log_incoming(update, "cooldown")
        return

    state.cooldowns[user.id] = now

    proof = state.fairness.next_spin(user.id, chat.id, message.message_id)
    item = state.loot_table.pick_by_unit_random(proof.r)

    anim_msg: Message | None = None
    try:
        with state.animation_path.open("rb") as animation_file:
            anim_msg = await message.reply_animation(animation=animation_file)
    except TelegramError as exc:
        logging.warning("failed_to_send_animation | error=%s", exc)

    await asyncio.sleep(DURATION_SECONDS)

    if anim_msg:
        try:
            await context.bot.delete_message(chat_id=chat.id, message_id=anim_msg.message_id)
        except TelegramError as exc:
            logging.warning("failed_to_delete_animation | chat_id=%s | error=%s", chat.id, exc)

    caption = (
        f"{item.name}\n"
        f"ID: {item.item_id}\n"
        f"Шанс (норм.): {state.loot_table.normalized_percent(item):.4f}%\n"
        f"Fairness: commit={state.fairness.commit}, nonce={proof.nonce}, client_seed={proof.client_seed}"
    )
    await send_item_photo(message, item, caption, state)

    logging.info(
        "spin_result | chat_id=%s | user_id=%s | username=%s | trigger=%s | nonce=%s | item_id=%s | item_name=%s | item_weight=%s | sum_weights=%s | commit=%s",
        chat.id,
        user.id,
        user.username,
        trigger,
        proof.nonce,
        item.item_id,
        item.name,
        item.weight,
        state.loot_table.total_weight,
        state.fairness.commit,
    )
    log_incoming(update, "handled_spin")


async def send_item_photo(message: Message, item: LootItem, caption: str, state: BotState) -> None:
    cached_file_id = state.file_id_cache.get(item.item_id)
    if cached_file_id:
        try:
            await message.reply_photo(photo=cached_file_id, caption=caption)
            return
        except TelegramError as exc:
            logging.warning("cached_file_id_failed | item_id=%s | error=%s", item.item_id, exc)

    with item.icon_path.open("rb") as photo_file:
        sent = await message.reply_photo(photo=photo_file, caption=caption)

    if sent.photo:
        state.file_id_cache[item.item_id] = sent.photo[-1].file_id
        save_file_id_cache(state.file_id_cache_path, state.file_id_cache)


async def handle_spin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_spin(update, context, trigger="command_/spin")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.text if update.effective_message else None
    if text == "хелп":
        await reply_help(update)
        log_incoming(update, "handled_help_text")
        return

    if text in {"спин", "сп", "рулетка"}:
        await handle_spin(update, context, trigger=f"text_{text}")
        return

    log_incoming(update, "ignored")


def main() -> None:
    setup_logging()
    token = get_token()
    state = build_state()

    app = Application.builder().token(token).build()
    app.bot_data["state"] = state

    app.add_handler(CommandHandler("help", handle_help_command))
    app.add_handler(CommandHandler("spin", handle_spin_command))
    app.add_handler(CommandHandler("reload", handle_reload_command))
    app.add_handler(CommandHandler("fair", handle_fair_command))
    app.add_handler(CommandHandler("reveal_seed", handle_reveal_seed_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logging.info("bot_started | mode=long_polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
