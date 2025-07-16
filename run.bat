@echo off
echo Запуск YouTube Subtitles Downloader...
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

REM Устанавливаем зависимости если нужно
echo Проверка зависимостей...
pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo Установка yt-dlp...
    pip install -r requirements.txt
)

REM Запускаем программу
echo Запуск программы...
python youtube_subtitles_downloader.py

pause