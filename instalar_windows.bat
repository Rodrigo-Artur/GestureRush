@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.11 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto falha
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto falha
python baixar_modelo.py
if errorlevel 1 goto falha
echo Instalacao concluida. Use jogar_windows.bat.
pause
exit /b 0
:falha
echo ERRO: verifique Python 3.11, internet e mensagens acima.
pause
exit /b 1
