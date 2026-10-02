@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha na instalacao.
  pause
  exit /b 1
)
echo Instalado. Execute run.bat.
pause
