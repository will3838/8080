codex/create-telegram-bot-with-long-polling-f8zdnd
# Telegram bot (Python, long polling)

Local Telegram bot project with one-click Windows startup and provably-fair roulette.

## Features

- `/help` -> strict response: `автор @HATE_death_ME`
- Text trigger `хелп` (exact match, lowercase only) -> same response as `/help`
- Roulette commands/triggers:
  - `/spin`
  - exact text `спин`, `сп`, `рулетка`
- User cooldown: 20 seconds per user (across all chats)
- Provably fair flow:
  - commit = `SHA256(server_seed)`
  - per-user nonce
  - deterministic client seed from update
  - `/fair` to inspect fairness info
  - `/reveal_seed` to reveal current seed and rotate to a new season commit
- Logging to console and `logs/bot.log`
- Works in private chats and groups

## Project structure

# Telegram-бот на Python (Long Polling)

Минимальный проект Telegram-бота для локального запуска на ПК.

## Что умеет бот

- Обрабатывает команду `/help` и отвечает строго:
  - `автор @HATE_death_ME`
- Обрабатывает текстовое сообщение **ровно** `хелп` (только в нижнем регистре, без пробелов) и отвечает так же, как `/help`.
- Работает в личных чатах и в группах.
- Использует **long polling** (без webhook).
- Логирует каждое входящее сообщение:
  - в консоль
  - в файл `logs/bot.log`

## Структура проекта
main

```text
.
├── bot.py
codex/create-telegram-bot-with-long-polling-f8zdnd
├── loot_table.py
├── fairness.py
├── roulette_animation.py
├── START_BOT.bat
├── requirements.txt
├── .env.example
├── README.md
├── logs/
├── data/
│   ├── items.xlsx                # required, create manually
│   └── file_id_cache.json        # auto-created
└── assets/
    ├── items/{id}.png            # required
    ├── generated/spin.mp4        # auto-generated at startup if missing
    ├── background.png            # optional
    └── frame.png                 # optional
```

## Windows: one-click startup

1. Unpack ZIP.
2. Double-click `START_BOT.bat` in project root.
3. Script will:
   - check required files,
   - create `.env` from `.env.example` (if needed),
   - open Notepad for token input,
   - detect/install Python 3.14 via WinGet,
   - create `.venv`, upgrade pip, install dependencies,
   - create `logs` folder,
   - run `bot.py`.

If Python was just installed and not visible in current PATH session, script asks to restart `START_BOT.bat`.

## Manual install and run

### 1) Create and activate virtual environment

**Linux/macOS**

codex/create-telegram-bot-with-long-polling-xil2gc
├── START_BOT.bat
main
├── requirements.txt
├── .env.example
├── README.md
└── logs/
```

codex/create-telegram-bot-with-long-polling-xil2gc
## Запуск на Windows в один клик

1. Распакуйте ZIP с проектом в любую папку.
2. Откройте папку проекта и запустите `START_BOT.bat` двойным кликом.
3. Скрипт автоматически:
   - проверит Python (`py`, затем `python`),
   - при необходимости попробует установить Python через **WinGet**,
   - создаст `.venv`, обновит `pip` и установит зависимости,
   - создаст `logs/` (если папки нет),
   - если `.env` отсутствует — скопирует `.env.example` в `.env`.
4. Если `.env` не было, скрипт откроет файл в Notepad:
   - вставьте токен в строку `TELEGRAM_BOT_TOKEN=...`,
   - сохраните файл,
   - закройте Notepad.
5. После этого бот запустится автоматически.

> Важно: скрипт использует WinGet для установки Python. После установки Python команда может стать доступной только в новом окне консоли — тогда скрипт подскажет перезапустить `START_BOT.bat`.

## Ручная установка и запуск
## Установка и запуск
main

### 1) Создайте и активируйте виртуальное окружение

#### Linux / macOS
main

```bash
python3 -m venv .venv
source .venv/bin/activate
```

codex/create-telegram-bot-with-long-polling-f8zdnd
**Windows (PowerShell)**

#### Windows (PowerShell)
main

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

codex/create-telegram-bot-with-long-polling-f8zdnd
### 2) Install dependencies

### 2) Установите зависимости
main

```bash
pip install -r requirements.txt
```

codex/create-telegram-bot-with-long-polling-f8zdnd
### 3) Create `.env`
### 3) Создайте `.env` из шаблона

#### Linux / macOS
main

```bash
cp .env.example .env
```

codex/create-telegram-bot-with-long-polling-f8zdnd
Put your token in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 4) Prepare data files

- Create `data/items.xlsx` manually.
- Put icons in `assets/items/{id}.png` for every item row.

### 5) Start bot

#### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

Откройте файл `.env` и вставьте токен вашего бота:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

### 4) Запустите бота
 main

```bash
python bot.py
```

codex/create-telegram-bot-with-long-polling-f8zdnd
## Excel format: `data/items.xlsx`

Use first worksheet. Columns are strict:

- `A: id` (unique; string or number, converted to string)
- `B: name` (string)
- `C: chance` (float, strict `0 < chance < 1`)

`chance` is used as **weight**, not percent.
Final probability = `weight_i / sum(weights)`.

Validation at startup and `/reload`:

- empty id/name/chance -> error
- chance `<= 0` or `>= 1` -> error
- duplicate id -> error
- missing icon `assets/items/{id}.png` -> error

If startup validation fails, bot does not start. If `/reload` fails, old table remains active.

## Commands

- `/help` -> `автор @HATE_death_ME`
- `/spin` -> spin flow (animation, wait 8s, delete animation if possible, send result)
- `/reload` -> reload Excel and rebuild weighted table (animation is NOT regenerated)
- `/fair` -> show commit, verification hint, user nonce
- `/reveal_seed` -> reveal current server seed, rotate to new seed+commit

## Provably fair notes

For each spin:

1. `nonce` increments per user.
2. `client_seed = "{user_id}:{chat_id}:{message_id}"`.
3. `digest = HMAC_SHA256(server_seed, "{client_seed}:{nonce}")`.
4. Convert digest to `r` in `[0, 1)`.
5. Weighted pick by prefix sums + binary search.

`/fair` shows current commit and current user nonce.
`/reveal_seed` reveals current `server_seed`, then bot generates new `server_seed` and commit.
Nonce counters are kept (not reset) by design.

После запуска бот начнёт получать обновления через long polling.

## Логирование

Логи пишутся одновременно:

- в консоль
- в файл `logs/bot.log`

Для каждого входящего сообщения фиксируются:

- дата/время
- `chat_id`
- `user_id` (если есть)
- `username` (если есть)
- текст сообщения
- действие (`handled_help_command`, `handled_help_text`, `ignored`)
 main
