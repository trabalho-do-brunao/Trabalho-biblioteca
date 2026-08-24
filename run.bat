@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual .venv nao encontrado.
    echo Execute setup.bat antes de iniciar o BiblioAvisa.
    exit /b 1
)

".venv\Scripts\python.exe" "scripts\iniciar_servicos.py"
set "EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %EXIT_CODE%
