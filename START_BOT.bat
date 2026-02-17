@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo ==============================================
echo Telegram Bot Launcher (Windows 10/11)
echo ==============================================
echo.

if not exist "bot.py" (
  echo [ERROR] bot.py not found. Run START_BOT.bat from project root.
  pause
  exit /b 1
)

if not exist "requirements.txt" (
  echo [ERROR] requirements.txt not found in project root.
  pause
  exit /b 1
)

if not exist ".env" (
  if not exist ".env.example" (
    echo [ERROR] .env.example not found.
    pause
    exit /b 1
  )
  copy /Y ".env.example" ".env" >nul
  if errorlevel 1 (
    echo [ERROR] Failed to create .env from .env.example.
    pause
    exit /b 1
  )
  echo [INFO] .env created. Notepad will open now.
  echo [INFO] Set TELEGRAM_BOT_TOKEN, save file, close Notepad, then continue.
  start /wait notepad ".env"
)

set "PY_CMD="
call :detect_python
if not defined PY_CMD (
  echo [INFO] Python not found. Trying WinGet install for Python 3.14...
  call :install_python
  if errorlevel 1 (
    echo [ERROR] Python install failed.
    pause
    exit /b 1
  )

  call :detect_python
  if not defined PY_CMD (
    echo [ERROR] Python was installed but not available in this shell yet.
    echo [INFO] Re-run START_BOT.bat.
    pause
    exit /b 1
  )
)

echo [OK] Python command: !PY_CMD!

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment .venv ...
  call !PY_CMD! -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv.
    pause
    exit /b 1
  )
)

echo [INFO] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] pip upgrade failed.
  pause
  exit /b 1
)

echo [INFO] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependency installation failed.
  pause
  exit /b 1
)

if not exist "logs" mkdir "logs"
if errorlevel 1 (
  echo [ERROR] Failed to create logs directory.
  pause
  exit /b 1
)

echo [INFO] Starting bot...
".venv\Scripts\python.exe" bot.py
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo [ERROR] Bot exited with code %EXIT_CODE%.
  pause
)
exit /b %EXIT_CODE%

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
  echo [ERROR] WinGet is not available. Install Python manually and re-run.
  exit /b 1
)

winget install -e --id Python.Python.3.14 --scope machine --accept-package-agreements --accept-source-agreements
if not errorlevel 1 exit /b 0

winget install -e --id Python.Python.3.14 --scope user --accept-package-agreements --accept-source-agreements
if not errorlevel 1 exit /b 0

winget install -e --id Python.PythonInstallManager --accept-package-agreements --accept-source-agreements
if errorlevel 1 exit /b 1

py install 3.14
if not errorlevel 1 exit /b 0

exit /b 1
