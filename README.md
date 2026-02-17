# Telegram loot bot (Python, long polling)

Бот работает локально, читает токен из `.env`, использует long polling и поддерживает команды `/help`, `/spin`, `/reload`, `/fair`, `/reveal_seed`.

## Windows: запуск в один клик

1. Распакуйте ZIP с проектом.
2. Дважды кликните `START_BOT.bat` в корне проекта.
3. Скрипт автоматически:
   - проверяет `py`/`python`;
   - при отсутствии Python пытается поставить Python 3.14 через WinGet;
   - при неуспехе пробует `PythonInstallManager` и `py install 3.14`;
   - создаёт `.venv`;
   - обновляет `pip`;
   - выполняет `pip install -r requirements.txt` на каждом запуске;
   - создаёт `logs/` (если нет) и запускает `bot.py`.
4. Если `.env` отсутствует, скрипт создаёт его из `.env.example`, открывает Notepad, ждёт закрытия файла и продолжает запуск.

> Если Python только что поставился и ещё не виден в PATH текущего окна, скрипт попросит перезапустить `START_BOT.bat`.

## Ручная установка и запуск

### 1) Создать виртуальное окружение

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Установить зависимости

```bash
pip install -r requirements.txt
```

### 3) Создать `.env`

```bash
cp .env.example .env
```

В `.env` укажите токен:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 4) Запустить

```bash
python bot.py
```

## Команды и триггеры

- `/help` → строго `автор @HATE_death_ME`
- Сообщение ровно `хелп` → как `/help`
- `/spin` → запуск рулетки
- Сообщения ровно `спин`, `сп`, `рулетка` → как `/spin`
- `/reload` → перечитать `data/items.xlsx` без перезапуска (анимация не пересоздаётся)
- `/fair` → commit, инструкция проверки, текущий nonce пользователя
- `/reveal_seed` → показать текущий `server_seed`, сразу сгенерировать новый seed/commit; nonce пользователей **не сбрасываются**

## Кулдаун

Для spin действует кулдаун 20 секунд на пользователя (во всех чатах). Если кулдаун активен, бот пишет сколько секунд осталось.

## Excel и ассеты

### Таблица предметов

Файл: `data/items.xlsx` (обязателен, бот не стартует без него).

Столбцы (строго):
- A: `id`
- B: `name`
- C: `chance` (вес, `0 < chance < 1`)

`chance` трактуется как **вес**, выбор идёт пропорционально `weight_i / sum(weights)`.

Валидация при старте и `/reload`:
- пустые `id/name/chance` запрещены;
- `chance <= 0` или `chance >= 1` запрещены;
- дубликаты `id` запрещены;
- обязательна иконка `assets/items/{id}.png` для каждого предмета.

### Иконки

- Путь: `assets/items/{id}.png`
- Формат: PNG
- Если хотя бы одного файла нет, загрузка таблицы не применяется.

## Анимация рулетки

- Файл: `assets/generated/spin.mp4`
- Параметры: 1280x720, 8 секунд, без звука.
- Генерируется **только при старте**, если файла нет.
- В `/spin` не генерируется заново.
- Можно подменить ассеты:
  - `assets/background.png` (опционально)
  - `assets/frame.png` (опционально)

`/spin` отправляет анимацию как animation, ждёт 8 секунд, пытается удалить сообщение с анимацией, затем отправляет результат.

## Проверяемая честность (provably fair)

- На старте:
  - генерируется `server_seed`
  - публикуется `commit = SHA256(server_seed)`
- Для каждого пользователя хранится `nonce` (счётчик спинов).
- На spin:
  - `client_seed = "{user_id}:{chat_id}:{message_id}"`
  - `nonce += 1`
  - `r` вычисляется через `HMAC_SHA256(server_seed, f"{client_seed}:{nonce}")`
  - предмет выбирается по весам (prefix sums + bisect)
- `/fair` показывает commit и nonce пользователя, но не раскрывает server_seed.
- `/reveal_seed` раскрывает текущий seed и открывает новый сезон (новый seed/new commit).

## Кэш file_id

- Файл: `data/file_id_cache.json`
- Ключ: `item_id`
- Значение: Telegram `file_id`
- Если `file_id` есть — отправка картинки по `file_id`.
- Иначе — отправка PNG с диска, затем сохранение `file_id` в кэш.

## Логи

Единый формат логирования в:
- консоль
- `logs/bot.log`

Логируется каждое входящее сообщение (chat_id/user_id/username/text/action) и отдельные записи по результатам spin.
