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

```text
.
├── bot.py
├── START_BOT.bat
├── requirements.txt
├── .env.example
├── README.md
└── logs/
```

## Запуск на Windows в один клик

1. Распакуйте ZIP с проектом.
2. Откройте папку проекта и запустите **`START_BOT.bat`** двойным кликом.
3. Скрипт автоматически:
   - проверит Python (сначала через `py`, затем через `python`),
   - при необходимости попробует установить Python через WinGet,
   - создаст `.venv`,
   - обновит `pip`,
   - установит зависимости из `requirements.txt`,
   - запустит бота.
4. Если файла `.env` нет, скрипт:
   - создаст `.env` из `.env.example`,
   - откроет `.env` в Notepad,
   - попросит вставить токен в `TELEGRAM_BOT_TOKEN=...`, сохранить и закрыть Notepad,
   - после этого продолжит запуск.

> Важно: скрипт использует **WinGet** для автоматической установки Python. После установки Python может потребоваться перезапустить `START_BOT.bat` (из-за обновления PATH в новой сессии).

## Установка и запуск вручную

### 1) Создайте и активируйте виртуальное окружение

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Установите зависимости

```bash
pip install -r requirements.txt
```

### 3) Создайте `.env` из шаблона

#### Linux / macOS

```bash
cp .env.example .env
```

#### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

Откройте файл `.env` и вставьте токен вашего бота:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

### 4) Запустите бота

```bash
python bot.py
```

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
