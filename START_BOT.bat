@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo ==============================================
echo Telegram Bot One-Click Launcher (Win10/11)
echo ==============================================

echo [STEP] Checking required project files...
if not exist "bot.py" (
  echo [ERROR] bot.py not found in project root.
  pause
  exit /b 1
)
if not exist "requirements.txt" (
  echo [ERROR] requirements.txt not found in project root.
  pause
  exit /b 1
)
if not exist ".env.example" (
  echo [ERROR] .env.example not found in project root.
  pause
  exit /b 1
)

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
    pause
    exit /b 1
  )

  call :detect_python
  if not defined PY_CMD (
    echo [ERROR] Python was installed but command is not available yet.
    echo [ERROR] Please restart START_BOT.bat.
    pause
    exit /b 1
  )
)

echo [OK] Using Python command: !PY_CMD!

if not exist ".venv\Scripts\python.exe" (
  echo [STEP] Creating virtual environment .venv...
  call !PY_CMD! -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv.
    pause
    exit /b 1
  )
)

echo [STEP] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo [ERROR] pip upgrade failed.
  pause
  exit /b 1
)

echo [STEP] Installing dependencies from requirements.txt...
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

echo [STEP] Starting bot...
".venv\Scripts\python.exe" bot.py
set "BOT_EXIT=%ERRORLEVEL%"
if not "%BOT_EXIT%"=="0" (
  echo [ERROR] Bot exited with code %BOT_EXIT%.
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
