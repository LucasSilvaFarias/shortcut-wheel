@echo off
title Radial Launcher - Instalacao
echo.
echo ==========================================
echo       RADIAL LAUNCHER - INSTALACAO
echo ==========================================
echo.

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo Python nao foi encontrado.
    echo Instale o Python 3.11+ e marque "Add Python to PATH".
    pause
    exit /b 1
)

echo Instalando PySide6...
py -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo Falha ao instalar as dependencias.
    pause
    exit /b 1
)

echo.
echo Instalacao concluida.
echo.
echo Para executar:
echo     py main.py
echo.
pause
