from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from fairness import FairnessEngine
from loot_table import Item, LootTable, load_loot_table
from roulette_animation import DURATION_SECONDS, generate_spin_animation

HELP_TEXT = "автор @HATE_death_ME"
SPIN_ALIASES = {"спин", "сп", "рулетка"}
COOLDOWN_SECONDS = 20

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "items"
GENERATED_SPIN_PATH = ASSETS_DIR / "generated" / "spin.mp4"
BACKGROUND_PATH = ASSETS_DIR / "background.png"
FRAME_PATH = ASSETS_DIR / "frame.png"
ITEMS_XLSX_PATH = DATA_DIR / "items.xlsx"
FILE_ID_CACHE_PATH = DATA_DIR / "file_id_cache.json"


@dataclass
class BotState:
    loot_table: LootTable
    fairness: FairnessEngine
    file_id_cache: dict[str, str] = field(default_factory=dict)
    cooldown_by_user: dict[int, float] = field(default_factory=dict)


STATE_LOCK = asyncio.Lock()


def setup_logging() -> None:
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(logs_dir / "bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)


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


def log_spin(
    update: Update,
    trigger: str,
    nonce: int,
    item: Item,
    sum_weights: float,
    commit: str,
) -> None:
    user = update.effective_user
    chat = update.effective_chat
    logging.info(
        "spin_result | chat_id=%s | user_id=%s | username=%s | trigger=%s | nonce=%s | item_id=%s | item_name=%s | item_weight=%s | sum_weights=%s | commit=%s",
        chat.id if chat else None,
        user.id if user else None,
        user.username if user else None,
        trigger,
        nonce,
        item.item_id,
        item.name,
        item.weight,
        sum_weights,
        commit,
    )


def load_file_id_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logging.warning("file_id cache is invalid JSON, reset cache")
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save_file_id_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def build_client_seed(update: Update) -> str:
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    user_id = user.id if user else 0
    chat_id = chat.id if chat else 0
    message_id = msg.message_id if msg else 0
    return f"{user_id}:{chat_id}:{message_id}"


def ensure_required_files() -> None:
    if not ITEMS_XLSX_PATH.exists():
        raise RuntimeError(f"Missing required Excel file: {ITEMS_XLSX_PATH}")


def build_state() -> BotState:
    loot_table = load_loot_table(ITEMS_XLSX_PATH, ICONS_DIR)
    fairness = FairnessEngine()
    cache = load_file_id_cache(FILE_ID_CACHE_PATH)
    logging.info("Fairness commit for current season: %s", fairness.commit)
    return BotState(loot_table=loot_table, fairness=fairness, file_id_cache=cache)


def ensure_animation(state: BotState) -> None:
    if GENERATED_SPIN_PATH.exists():
        logging.info("Animation already exists: %s", GENERATED_SPIN_PATH)
        return

    logging.info("Generating roulette animation at startup: %s", GENERATED_SPIN_PATH)
    generate_spin_animation(
        items=state.loot_table.items,
        output_path=GENERATED_SPIN_PATH,
        background_path=BACKGROUND_PATH,
        frame_path=FRAME_PATH,
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(HELP_TEXT)
    log_incoming(update, "handled_help_command")


async def handle_fair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        log_incoming(update, "ignored")
        return

    state: BotState = context.application.bot_data["state"]
    async with STATE_LOCK:
        nonce = state.fairness.current_nonce(user.id)
        commit = state.fairness.commit

    text = (
        "Provably fair\n"
        f"commit: {commit}\n"
        f"your_nonce: {nonce}\n"
        "verify: r = HMAC_SHA256(server_seed, f\"client_seed:nonce\"); convert to [0,1), then weighted pick\n"
        "server_seed hidden until /reveal_seed"
    )
    await update.effective_message.reply_text(text)
    log_incoming(update, "handled_fair")


async def handle_reveal_seed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: BotState = context.application.bot_data["state"]
    async with STATE_LOCK:
        old_seed, old_commit, new_commit = state.fairness.reveal_and_rotate_seed()

    text = (
        f"reveal_server_seed: {old_seed}\n"
        f"old_commit: {old_commit}\n"
        f"new_commit: {new_commit}\n"
        "nonce counters are NOT reset"
    )
    await update.effective_message.reply_text(text)
    log_incoming(update, "handled_reveal_seed")


async def handle_reload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: BotState = context.application.bot_data["state"]
    try:
        new_table = load_loot_table(ITEMS_XLSX_PATH, ICONS_DIR)
    except Exception as exc:
        await update.effective_message.reply_text(f"reload failed: {exc}")
        log_incoming(update, "reload_failed")
        return

    async with STATE_LOCK:
        state.loot_table = new_table

    await update.effective_message.reply_text("reload ok")
    log_incoming(update, "handled_reload")


async def _try_delete_message(bot_message: Message) -> None:
    try:
        await bot_message.delete()
    except TelegramError as exc:
        logging.warning("cannot delete animation message: %s", exc)


async def _send_item_result(update: Update, context: ContextTypes.DEFAULT_TYPE, item: Item, normalized_pct: float, nonce: int, client_seed: str, commit: str) -> None:
    state: BotState = context.application.bot_data["state"]
    caption = (
        f"{item.name}\n"
        f"ID: {item.item_id}\n"
        f"Шанс (норм.): {normalized_pct:.6f}%\n"
        f"fairness: commit={commit}, nonce={nonce}, client_seed={client_seed}"
    )

    file_id = state.file_id_cache.get(item.item_id)
    sent: Message
    if file_id:
        sent = await update.effective_message.reply_photo(photo=file_id, caption=caption)
    else:
        with item.icon_path.open("rb") as f:
            sent = await update.effective_message.reply_photo(photo=f, caption=caption)

    if sent.photo:
        new_file_id = sent.photo[-1].file_id
        if state.file_id_cache.get(item.item_id) != new_file_id:
            state.file_id_cache[item.item_id] = new_file_id
            save_file_id_cache(FILE_ID_CACHE_PATH, state.file_id_cache)


async def spin_once(update: Update, context: ContextTypes.DEFAULT_TYPE, trigger: str) -> None:
    user = update.effective_user
    if not user:
        log_incoming(update, "ignored")
        return

    state: BotState = context.application.bot_data["state"]
    now = time.monotonic()

    async with STATE_LOCK:
        last = state.cooldown_by_user.get(user.id, 0.0)
        left = COOLDOWN_SECONDS - (now - last)
        if left > 0:
            await update.effective_message.reply_text(f"Cooldown: {int(left) + 1}s")
            log_incoming(update, "cooldown")
            return

        state.cooldown_by_user[user.id] = now
        nonce = state.fairness.next_nonce(user.id)
        client_seed = build_client_seed(update)
        digest = state.fairness.digest_for_spin(client_seed, nonce)
        r = state.fairness.digest_to_unit_float(digest)
        item = state.loot_table.choose_by_r(r)
        normalized_pct = (item.weight / state.loot_table.sum_weights) * 100
        commit = state.fairness.commit
        sum_weights = state.loot_table.sum_weights

    log_spin(update, trigger, nonce, item, sum_weights, commit)
    log_incoming(update, "handled_spin")

    with GENERATED_SPIN_PATH.open("rb") as anim_file:
        anim_message = await update.effective_message.reply_animation(animation=anim_file)

    await asyncio.sleep(DURATION_SECONDS)
    await _try_delete_message(anim_message)

    await _send_item_result(update, context, item, normalized_pct, nonce, client_seed, commit)


async def handle_spin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await spin_once(update, context, trigger="/spin")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.text if update.effective_message else ""
    if text == "хелп":
        await update.effective_message.reply_text(HELP_TEXT)
        log_incoming(update, "handled_help_text")
        return

    if text in SPIN_ALIASES:
        await spin_once(update, context, trigger=text)
        return

    log_incoming(update, "ignored")


def get_token() -> str:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
    return token


def main() -> None:
    setup_logging()
    ensure_required_files()
    state = build_state()
    ensure_animation(state)
    token = get_token()

    app = Application.builder().token(token).build()
    app.bot_data["state"] = state

    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("spin", handle_spin))
    app.add_handler(CommandHandler("reload", handle_reload))
    app.add_handler(CommandHandler("fair", handle_fair))
    app.add_handler(CommandHandler("reveal_seed", handle_reveal_seed))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logging.info("Bot started with long polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
