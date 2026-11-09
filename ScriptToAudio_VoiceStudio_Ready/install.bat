@echo off
cd /d "%~dp0"
title ScriptToAudio Voice Studio - Install
echo ============================================
echo ScriptToAudio Voice Studio - Setup
echo ============================================
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3.11 -m venv .venv
  if errorlevel 1 py -3 -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  echo Could not create Python venv. Install Python 3.11 and retry.
  pause
  exit /b 1
)
echo Installing lightweight website dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
 echo Setup failed. Check internet and the error above.
 pause
 exit /b 1
)
echo.
echo Setup complete. Voice cloning XTTS is optional and may need separate troubleshooting.
pause
