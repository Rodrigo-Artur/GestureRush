@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Instale primeiro com instalar_windows.bat
  pause
  exit /b 1
)
.venv\Scripts\python.exe main.py %*
if errorlevel 1 pause
