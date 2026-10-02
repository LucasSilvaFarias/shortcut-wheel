@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher ^(py^) nao foi encontrado.
    echo Instale o Python e marque a opcao para instalar o Python Launcher.
    pause
    exit /b 1
)

echo Instalando dependencias...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo.
    echo Falha ao instalar as dependencias do build.
    pause
    exit /b 1
)

echo.
echo Gerando RadialLauncher.exe...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name RadialLauncher --icon "%~dp0radial.ico" --add-data "%~dp0radial.ico;." "%~dp0main.py"
if errorlevel 1 (
    echo.
    echo Falha ao gerar RadialLauncher.exe.
    pause
    exit /b 1
)

if not exist "%~dp0dist\RadialLauncher.exe" (
    echo.
    echo O build terminou sem gerar dist\RadialLauncher.exe.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo EXE criado em:
echo "%~dp0dist\RadialLauncher.exe"
echo ==========================================
pause
