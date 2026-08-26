@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title BiblioAvisa - Configuracao do ambiente

echo ======================================================
echo          BiblioAvisa - Configuracao do ambiente
echo ======================================================
echo.

rem ------------------------------------------------------
rem 1. Localizar Python, Node.js e npm
rem ------------------------------------------------------
set "PY_CMD="

where py >nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3"

if not defined PY_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD goto :python_missing
where node >nul 2>&1
if errorlevel 1 goto :node_missing
where npm.cmd >nul 2>&1
if errorlevel 1 goto :npm_missing

echo [OK] Python encontrado.
echo [OK] Node.js encontrado.
echo [OK] npm encontrado.

rem ------------------------------------------------------
rem 2. Conferir arquivos essenciais do projeto
rem ------------------------------------------------------
if not exist "requirements.txt" goto :requirements_missing
if not exist ".env.example" goto :env_example_missing
if not exist "scripts\init_db.py" goto :init_db_missing
if not exist "whatsapp_service\package.json" goto :package_json_missing

rem ------------------------------------------------------
rem 3. Criar ambiente virtual local, se necessario
rem ------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Criando ambiente virtual .venv...
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :venv_error
    echo [OK] Ambiente virtual criado.
) else (
    echo [OK] Ambiente virtual .venv ja existe.
)

set "VENV_PY=%CD%\.venv\Scripts\python.exe"

rem ------------------------------------------------------
rem 4. Instalar ou atualizar as dependencias Python
rem ------------------------------------------------------
echo [INFO] Instalando dependencias Python de requirements.txt...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :pip_error

echo [OK] Dependencias Python instaladas.

rem ------------------------------------------------------
rem 5. Instalar ou atualizar as dependencias do WhatsApp
rem ------------------------------------------------------
echo.
echo [INFO] Instalando dependencias do servico WhatsApp...
pushd "whatsapp_service"
call npm.cmd install
if errorlevel 1 (
    popd
    goto :npm_install_error
)
popd

echo [OK] Dependencias do WhatsApp instaladas.

rem ------------------------------------------------------
rem 6. Criar o arquivo .env local, se ainda nao existir
rem ------------------------------------------------------
if not exist ".env" (
    echo [INFO] Arquivo .env nao encontrado.
    copy /Y ".env.example" ".env" >nul
    echo [OK] Arquivo .env criado a partir de .env.example.
    echo.
    echo ------------------------------------------------------
    echo ATENCAO: configure os valores locais do .env.
    echo Principalmente DB_PASSWORD com a senha do PostgreSQL.
    echo O arquivo sera aberto no Bloco de Notas.
    echo Salve o arquivo e depois volte para esta janela.
    echo ------------------------------------------------------
    echo.
    start "" notepad.exe ".env"
    pause
) else (
    echo [OK] Arquivo .env ja existe e sera preservado.
)

rem ------------------------------------------------------
rem 7. Impedir tentativa com senha vazia ou de exemplo
rem ------------------------------------------------------
findstr /C:"DB_PASSWORD=preencha_localmente" ".env" >nul 2>&1
if not errorlevel 1 goto :env_pending

findstr /C:"DB_PASSWORD=troque_esta_senha" ".env" >nul 2>&1
if not errorlevel 1 goto :env_pending

findstr /R /C:"^DB_PASSWORD=$" ".env" >nul 2>&1
if not errorlevel 1 goto :env_pending

rem ------------------------------------------------------
rem 8. Inicializar e validar o banco PostgreSQL
rem ------------------------------------------------------
echo.
echo [INFO] Inicializando o banco PostgreSQL...
"%VENV_PY%" "scripts\init_db.py"
if errorlevel 1 goto :database_error

rem ------------------------------------------------------
rem 9. Finalizacao
rem ------------------------------------------------------
echo.
echo ======================================================
echo [OK] Ambiente do BiblioAvisa preparado com sucesso.
echo ======================================================
echo.
echo Agora inicie o sistema pela raiz com:
echo     run.bat
echo.
echo Se o projeto for atualizado futuramente, voce pode
 echo executar setup.bat novamente para sincronizar as
 echo dependencias e validar o banco sem apagar seu .env.
echo.
pause
exit /b 0

:python_missing
echo [ERRO] Python 3 nao foi encontrado neste computador.
echo Instale Python 3.10 ou superior e tente novamente.
goto :end_error

:node_missing
echo [ERRO] Node.js nao foi encontrado neste computador.
echo Instale Node.js 20 ou superior e tente novamente.
goto :end_error

:npm_missing
echo [ERRO] npm nao foi encontrado neste computador.
echo Reinstale o Node.js com o npm habilitado e tente novamente.
goto :end_error

:requirements_missing
echo [ERRO] requirements.txt nao foi encontrado na raiz do projeto.
goto :end_error

:env_example_missing
echo [ERRO] .env.example nao foi encontrado na raiz do projeto.
goto :end_error

:init_db_missing
echo [ERRO] scripts\init_db.py nao foi encontrado.
goto :end_error

:package_json_missing
echo [ERRO] whatsapp_service\package.json nao foi encontrado.
goto :end_error

:venv_error
echo [ERRO] Nao foi possivel criar o ambiente virtual .venv.
goto :end_error

:pip_error
echo [ERRO] Nao foi possivel instalar as dependencias Python.
goto :end_error

:npm_install_error
echo [ERRO] Nao foi possivel instalar as dependencias do WhatsApp.
echo Confira sua conexao e a instalacao do Node.js/npm.
goto :end_error

:env_pending
echo.
echo [ATENCAO] O arquivo .env ainda nao possui uma senha valida.
echo Edite DB_PASSWORD com a senha do PostgreSQL deste computador.
echo Depois execute setup.bat novamente.
echo.
start "" notepad.exe ".env"
goto :end_error

:database_error
echo.
echo [ERRO] A inicializacao do PostgreSQL falhou.
echo Confira se o PostgreSQL esta iniciado e se os dados do .env estao corretos.
echo Nenhuma senha deve ser enviada para o GitHub.
goto :end_error

:end_error
echo.
pause
exit /b 1
