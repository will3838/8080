@echo off
setlocal EnableExtensions EnableDelayedExpansion
codex/create-telegram-bot-with-long-polling-f8zdnd

cd /d "%~dp0"

echo ==============================================
echo Telegram Bot One-Click Launcher (Win10/11)
echo ==============================================

echo [STEP] Checking required project files...
if not exist "bot.py" (
  echo [ERROR] bot.py not found in project root.

chcp 65001 >nul

cd /d "%~dp0"

echo ================================================
echo Telegram Bot Launcher (Windows 10/11)
echo ================================================

echo [INFO] Проверка структуры проекта...
if not exist "bot.py" (
  echo [ERROR] Не найден bot.py. Запускайте START_BOT.bat из корня проекта.
 main
  pause
  exit /b 1
)
if not exist "requirements.txt" (
codex/create-telegram-bot-with-long-polling-f8zdnd
  echo [ERROR] requirements.txt not found in project root.

  echo [ERROR] Не найден requirements.txt.
main
  pause
  exit /b 1
)
if not exist ".env.example" (
 codex/create-telegram-bot-with-long-polling-f8zdnd
  echo [ERROR] .env.example not found in project root.

main
  pause
  exit /b 1
)

codex/create-telegram-bot-with-long-polling-f8zdnd
if not exist ".env" (
  echo [STEP] .env not found. Creating from .env.example...
  copy /Y ".env.example" ".env" >nul
  if errorlevel 1 (
    echo [ERROR] Failed to create .env from .env.example.
    pause
    exit /b 1
  )
  echo [STEP] Opening .env in Notepad. Paste your bot token and save file.
  start /wait notepad ".env"
)

set "PY_CMD="
call :detect_python
if not defined PY_CMD (
  echo [STEP] Python not found. Trying install via winget...
  call :install_python
  if errorlevel 1 (
    echo [ERROR] Python install failed.

set "PYTHON_CMD="
call :detect_python
if not defined PYTHON_CMD (
  echo [WARN] Python не найден. Попытка автоматической установки через WinGet...
  call :install_python
  if errorlevel 1 (
    echo [ERROR] Не удалось установить Python автоматически.
main
    pause
    exit /b 1
  )

  call :detect_python
codex/create-telegram-bot-with-long-polling-f8zdnd
  if not defined PY_CMD (
    echo [ERROR] Python was installed but command is not available yet.
    echo [ERROR] Please restart START_BOT.bat.

  if not defined PYTHON_CMD (
    echo [WARN] Python установлен, но команда ещё недоступна в текущем окне.
    echo [INFO] Перезапусти START_BOT.bat.
main
    pause
    exit /b 1
  )
)

codex/create-telegram-bot-with-long-polling-f8zdnd
echo [OK] Using Python command: !PY_CMD!

if not exist ".venv\Scripts\python.exe" (
  echo [STEP] Creating virtual environment .venv...
  call !PY_CMD! -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv.

echo [INFO] Используется интерпретатор: %PYTHON_CMD%

echo [INFO] Проверка виртуального окружения (.venv)...
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Создаю .venv...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Не удалось создать виртуальное окружение .venv.
main
    pause
    exit /b 1
  )
)

codex/create-telegram-bot-with-long-polling-f8zdnd
echo [STEP] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] pip upgrade failed.

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] После создания .venv не найден .venv\Scripts\python.exe.
main
  pause
  exit /b 1
)

codex/create-telegram-bot-with-long-polling-f8zdnd
echo [STEP] Installing dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed.

echo [INFO] Обновляю pip...
.venv\Scripts\python -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Не удалось обновить pip.
main
  pause
  exit /b 1
)

codex/create-telegram-bot-with-long-polling-f8zdnd
if not exist "logs" mkdir "logs"
if errorlevel 1 (
  echo [ERROR] Failed to create logs directory.

echo [INFO] Устанавливаю зависимости из requirements.txt...
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Не удалось установить зависимости.
main
  pause
  exit /b 1
)

codex/create-telegram-bot-with-long-polling-f8zdnd
echo [STEP] Starting bot...
".venv\Scripts\python.exe" bot.py
set "BOT_EXIT=%ERRORLEVEL%"
if not "%BOT_EXIT%"=="0" (
  echo [ERROR] Bot exited with code %BOT_EXIT%.
  pause
  exit /b %BOT_EXIT%
if not exist "logs" (
  echo [INFO] Создаю папку logs...
  mkdir logs
  if errorlevel 1 (
    echo [ERROR] Не удалось создать папку logs.
    pause
    exit /b 1
  )
)

if not exist ".env" (
  echo [INFO] Файл .env не найден. Создаю из .env.example...
  copy /Y ".env.example" ".env" >nul
  if errorlevel 1 (
    echo [ERROR] Не удалось создать .env.
    pause
    exit /b 1
  )

  echo [ACTION] Сейчас откроется Notepad с файлом .env.
  echo [ACTION] Вставьте токен бота в TELEGRAM_BOT_TOKEN=..., сохраните файл и закройте Notepad.
  start /wait notepad ".env"

  echo [INFO] Если токен добавлен, нажмите любую клавишу для продолжения...
  pause >nul
)

echo [INFO] Запускаю бота...
.venv\Scripts\python bot.py
set "BOT_EXIT_CODE=%ERRORLEVEL%"

if not "%BOT_EXIT_CODE%"=="0" (
  echo [ERROR] Бот завершился с кодом %BOT_EXIT_CODE%.
  pause
  exit /b %BOT_EXIT_CODE%
main
)

exit /b 0

:detect_python
codex/create-telegram-bot-with-long-polling-f8zdnd
set "PY_CMD="
py -3.14 --version >nul 2>&1
if not errorlevel 1 (
  set "PY_CMD=py -3.14"
  exit /b 0
)
py --version >nul 2>&1
if not errorlevel 1 (
  set "PY_CMD=py"
  exit /b 0
)
python --version >nul 2>&1
if not errorlevel 1 (
  set "PY_CMD=python"
  exit /b 0
)
exit /b 1

:install_python
where winget >nul 2>&1
if errorlevel 1 (
  echo [ERROR] winget is not available. Install Python manually and re-run script.
  exit /b 1
)

echo [STEP] Installing Python 3.14 via winget (machine scope)...
winget install -e --id Python.Python.3.14 --scope machine --accept-package-agreements --accept-source-agreements
if not errorlevel 1 exit /b 0

echo [STEP] Machine scope failed. Trying user scope...
winget install -e --id Python.Python.3.14 --scope user --accept-package-agreements --accept-source-agreements
if not errorlevel 1 exit /b 0

echo [STEP] Python direct install failed. Trying PythonInstallManager...
winget install -e --id Python.PythonInstallManager --accept-package-agreements --accept-source-agreements
if errorlevel 1 exit /b 1

py install 3.14
if not errorlevel 1 exit /b 0

exit /b 1

set "PYTHON_CMD="
py -3 --version >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_CMD=py -3"
  goto :eof
)

python --version >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_CMD=python"
)
goto :eof

:install_python
echo [INFO] Проверка наличия WinGet...
winget --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] WinGet не найден или не работает. Установите Python вручную и запустите START_BOT.bat снова.
  exit /b 1
)

set "WINGET_SCOPE=machine"
net session >nul 2>&1
if errorlevel 1 (
  set "WINGET_SCOPE=user"
  echo [WARN] Админ-права не обнаружены. Будет использован scope=user.
) else (
  echo [INFO] Админ-права обнаружены. Будет использован scope=machine.
)

echo [INFO] Попытка установить Python 3.14 через WinGet...
winget install -e --id Python.Python.3.14 --scope %WINGET_SCOPE% --accept-package-agreements --accept-source-agreements
if not errorlevel 1 (
  echo [OK] Python 3.14 установлен через WinGet.
  exit /b 0
)

echo [WARN] Установка Python 3.14 напрямую не удалась.
echo [INFO] Пробую установить Python Install Manager...
winget install -e --id Python.PythonInstallManager --scope %WINGET_SCOPE% --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo [ERROR] Не удалось установить Python Install Manager через WinGet.
  exit /b 1
)

echo [INFO] Устанавливаю Python 3.14 через py install 3.14...
py install 3.14
if errorlevel 1 (
  echo [ERROR] Команда py install 3.14 завершилась с ошибкой.
  exit /b 1
)

echo [OK] Python 3.14 установлен через Python Install Manager.
exit /b 0
main
