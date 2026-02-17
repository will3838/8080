@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0"

echo ================================================
echo Telegram Bot Launcher (Windows 10/11)
echo ================================================

echo [INFO] Проверка структуры проекта...
if not exist "bot.py" (
  echo [ERROR] Не найден bot.py. Запускайте START_BOT.bat из корня проекта.
  pause
  exit /b 1
)
if not exist "requirements.txt" (
  echo [ERROR] Не найден requirements.txt.
  pause
  exit /b 1
)
if not exist ".env.example" (
  echo [ERROR] Не найден .env.example.
  pause
  exit /b 1
)

set "PYTHON_CMD="
call :detect_python
if not defined PYTHON_CMD (
  echo [WARN] Python не найден. Попытка автоматической установки через WinGet...
  call :install_python
  if errorlevel 1 (
    echo [ERROR] Не удалось установить Python автоматически.
    pause
    exit /b 1
  )

  call :detect_python
  if not defined PYTHON_CMD (
    echo [WARN] Python установлен, но команда ещё недоступна в текущем окне.
    echo [INFO] Перезапусти START_BOT.bat.
    pause
    exit /b 1
  )
)

echo [INFO] Используется интерпретатор: %PYTHON_CMD%

echo [INFO] Проверка виртуального окружения (.venv)...
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Создаю .venv...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Не удалось создать виртуальное окружение .venv.
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] После создания .venv не найден .venv\Scripts\python.exe.
  pause
  exit /b 1
)

echo [INFO] Обновляю pip...
.venv\Scripts\python -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Не удалось обновить pip.
  pause
  exit /b 1
)

echo [INFO] Устанавливаю зависимости из requirements.txt...
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Не удалось установить зависимости.
  pause
  exit /b 1
)

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
)

exit /b 0

:detect_python
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
