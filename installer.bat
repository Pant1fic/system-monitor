@echo off
echo ========================================
echo    System Monitor Auto-Installer
echo ========================================
echo.

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo Устанавливаем Python...
    powershell -Command "Start-Process 'https://www.python.org/ftp/python/3.14.0/python-3.14.0-amd64.exe' -Wait"
    echo Пожалуйста, завершите установку Python и запустите этот файл снова.
    pause
    exit
)

:: Проверяем pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ PIP не найден!
    echo Устанавливаем pip...
    python -m ensurepip --default-pip
)

:: Устанавливаем библиотеки
echo 📦 Устанавливаем необходимые библиотеки...
pip install psutil

:: Собираем в EXE
echo 🔨 Собираем программу...
pip install pyinstaller
pyinstaller --onefile --windowed --name "SystemMonitor" pcmonitor.py

echo.
echo ✅ Готово! Программа находится в папке 'dist'
echo 🚀 Запускаем SystemMonitor.exe...
start dist\SystemMonitor.exe

pause