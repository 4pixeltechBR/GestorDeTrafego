@echo off
title Gestor de Trafego IA
color 0A
echo.
echo  ============================================
echo   🚀 GESTOR DE TRÁFEGO IA
echo   Copiloto de Tráfego Pago com IA
echo  ============================================
echo.

:: Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ❌ Python não encontrado!
    echo  Instale em: https://www.python.org/downloads/
    pause
    exit /b
)

:: Verifica se venv existe, senão cria
if not exist "venv" (
    echo  📦 Criando ambiente virtual...
    python -m venv venv
    echo  ✅ Ambiente virtual criado!
    echo.
)

:: Ativa o venv
call venv\Scripts\activate.bat

:: Verifica se dependências estão instaladas
if not exist "venv\Lib\site-packages\fastapi" (
    echo  📦 Instalando dependências...
    pip install -r requirements.txt --quiet
    echo  ✅ Dependências instaladas!
    echo.
)

:: Verifica se .env existe
if not exist ".env" (
    echo  ⚠️  Arquivo .env não encontrado!
    echo  Copiando .env.example para .env...
    copy .env.example .env
    echo.
    echo  📝 IMPORTANTE: Edite o arquivo .env com suas API Keys!
    echo  Abra com: notepad .env
    echo.
    pause
)

:: Inicia o servidor
echo  🚀 Iniciando servidor em http://localhost:8080
echo  📖 Documentação da API: http://localhost:8080/docs
echo  Pressione Ctrl+C para parar.
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

pause
