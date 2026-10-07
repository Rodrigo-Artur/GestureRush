@echo off
setlocal
title Gesture Rush - Gerador de Executavel

cd /d "%~dp0"

echo ================================
echo   GERADOR DO GESTURE RUSH
echo ================================
echo.

if not exist "main.py" (
    echo ERRO: main.py nao encontrado.
    pause
    exit /b 1
)

if not exist "modelos\hand_landmarker.task" (
    echo ERRO: modelo do MediaPipe nao encontrado.
    echo Execute instalar_windows.bat primeiro.
    pause
    exit /b 1
)

if not exist "assets" (
    echo ERRO: pasta assets nao encontrada.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo Verificando Python...
"%PYTHON%" --version
if errorlevel 1 goto erro

echo.
echo Instalando ou verificando PyInstaller...
"%PYTHON%" -m pip install pyinstaller
if errorlevel 1 goto erro

echo.
echo Gerando executavel...
"%PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --name GestureRush ^
    --icon "assets\definitivos\marca\17_GestureRush.ico" ^
    --collect-all mediapipe ^
    --collect-all pygame ^
    --collect-all cv2 ^
    --add-data "modelos\hand_landmarker.task;modelos" ^
    --add-data "assets;assets" ^
    main.py

if errorlevel 1 goto erro

echo.
echo ================================
echo   EXECUTAVEL GERADO!
echo ================================
echo.
echo Local: dist\GestureRush\GestureRush.exe
echo Copie a pasta dist\GestureRush inteira para outro PC.
pause
exit /b 0

:erro
echo.
echo Falha durante a geracao do executavel.
pause
exit /b 1
