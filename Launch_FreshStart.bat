@echo off
title FreshStart — Launcher
echo Checking for Python...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Opening download page...
    start https://www.python.org/downloads/
    echo.
    echo Install Python, then re-run this script.
    echo Make sure to check "Add Python to PATH" during install!
    pause
    exit
)

echo Python found. Launching FreshStart...
python "%~dp0setup_installer.py"
pause
