@echo off
title Gestor de Trafego IA
color 0A
echo.
echo  ============================================
echo   GESTOR DE TRAFEGO IA — Telegram Bot
echo  ============================================
echo.

:: Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERRO: Python nao encontrado!
    echo  Instale em: https://www.python.org/downloads/
    pause
    exit /b
)

:: Cria venv se nao existir
if not exist "venv" (
    echo  Criando ambiente virtual...
    python -m venv venv
    echo  Ambiente virtual criado!
    echo.
)

:: Ativa venv
call venv\Scripts\activate.bat

:: Instala dependencias se necessario
if not exist "venv\Lib\site-packages\telegram" (
    echo  Instalando dependencias...
    pip install -r requirements.txt --quiet
    echo  Dependencias instaladas!
    echo.
)

:: Verifica .env
if not exist ".env" (
    echo  Arquivo .env nao encontrado!
    echo  Criando a partir do .env.example...
    copy .env.example .env
    echo.
    echo  IMPORTANTE: Edite o .env com suas chaves antes de continuar!
    echo  Abra com: notepad .env
    echo.
    pause
    exit /b
)

:: Inicia o bot
echo  Iniciando GestorDeTrafego via Telegram...
echo  Pressione Ctrl+C para parar.
echo.
python bot.py

pause
