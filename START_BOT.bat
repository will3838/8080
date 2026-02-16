@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cd /d "%~dp0"

echo ==============================================
echo   Telegram Bot Launcher (Windows 10/11)
echo ==============================================
echo.

if not exist "bot.py" (
  echo [ERROR] Не найден bot.py. Запускайте START_BOT.bat из корня проекта.
  pause
  exit /b 1
)

if not exist "requirements.txt" (
  echo [ERROR] Не найден requirements.txt в корне проекта.
  pause
  exit /b 1
)

set "PY_CMD="
set "PY_INSTALLED_NOW=0"

echo [1/7] Проверка Python...
call :detect_python
if defined PY_CMD (
  echo [OK] Найден интерпретатор: !PY_CMD!
) else (
  echo [INFO] Python не найден. Попытка автоматической установки через WinGet...
  call :install_python
  if errorlevel 1 (
    echo [ERROR] Не удалось установить Python автоматически.
    pause
    exit /b 1
  )

  set "PY_INSTALLED_NOW=1"
  call :detect_python
  if not defined PY_CMD (
    echo [WARN] Python установлен, но команда пока не доступна в текущей сессии.
    echo [ACTION] Перезапусти START_BOT.bat.
    pause
    exit /b 1
  )

  echo [OK] Python успешно установлен и доступен: !PY_CMD!
)

echo.
echo [2/7] Проверка виртуального окружения .venv...
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] .venv не найден. Создаю...
  call !PY_CMD! -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Не удалось создать виртуальное окружение .venv
    pause
    exit /b 1
  )
  echo [OK] Виртуальное окружение создано.
) else (
  echo [OK] .venv уже существует.
)

echo.
echo [3/7] Обновление pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] Не удалось обновить pip.
  pause
  exit /b 1
)

echo.
echo [4/7] Установка зависимостей из requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Не удалось установить зависимости.
  pause
  exit /b 1
)

echo.
echo [5/7] Проверка .env...
if not exist ".env" (
  if not exist ".env.example" (
    echo [ERROR] Не найден .env.example для создания .env
    pause
    exit /b 1
  )

  copy /Y ".env.example" ".env" >nul
  if errorlevel 1 (
    echo [ERROR] Не удалось создать .env из .env.example
    pause
    exit /b 1
  )

  echo [INFO] Файл .env создан.
  echo [ACTION] Сейчас откроется Notepad. Вставьте токен в TELEGRAM_BOT_TOKEN, сохраните файл и закройте Notepad.
  start /wait notepad ".env"
  echo [INFO] Возврат из Notepad. Нажмите любую клавишу для продолжения запуска.
  pause >nul
) else (
  echo [OK] .env уже существует.
)

echo.
echo [6/7] Проверка папки logs...
if not exist "logs" mkdir "logs"
if errorlevel 1 (
  echo [ERROR] Не удалось создать папку logs.
  pause
  exit /b 1
)

echo [7/7] Запуск бота...
echo ----------------------------------------------
".venv\Scripts\python.exe" bot.py
set "BOT_EXIT=%ERRORLEVEL%"
echo ----------------------------------------------
if not "%BOT_EXIT%"=="0" (
  echo [ERROR] Бот завершился с кодом %BOT_EXIT%.
  pause
  exit /b %BOT_EXIT%
)

exit /b 0

:detect_python
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
  echo [ERROR] WinGet не найден. Установите Python вручную и запустите START_BOT.bat снова.
  exit /b 1
)

echo [INFO] Попытка: WinGet -> Python 3.14 (machine scope)...
winget install -e --id Python.Python.3.14 --scope machine --accept-package-agreements --accept-source-agreements
if not errorlevel 1 (
  echo [OK] Python 3.14 установлен (machine scope).
  exit /b 0
)

echo [WARN] Установка с machine scope не удалась. Пробую user scope...
winget install -e --id Python.Python.3.14 --scope user --accept-package-agreements --accept-source-agreements
if not errorlevel 1 (
  echo [OK] Python 3.14 установлен (user scope).
  exit /b 0
)

echo [WARN] Прямая установка Python 3.14 не удалась. Пробую через Python Install Manager...
winget install -e --id Python.PythonInstallManager --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo [ERROR] Не удалось установить Python Install Manager.
  exit /b 1
)

py install 3.14
if not errorlevel 1 (
  echo [OK] Python 3.14 установлен через Python Install Manager.
  exit /b 0
)

echo [ERROR] Не удалось установить Python 3.14 через Python Install Manager.
exit /b 1
