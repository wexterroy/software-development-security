@echo off
cd /d %~dp0
chcp 65001 >nul

echo [1/5] Создание виртуального окружения...
if not exist venv (
    python -m venv venv
)

echo [2/5] Активация виртуального окружения...
call venv\Scripts\activate.bat

echo [3/5] Обновление pip...
python -m pip install --upgrade pip

echo [4/5] Установка зависимостей...
pip install -r requirements.txt

echo [5/5] Запуск сервера...
python server.py

pause
