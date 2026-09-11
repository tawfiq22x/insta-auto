@echo off
setlocal
title Instagram Bot Updater
color 0B
cd /d "%~dp0"

echo ==================================================
echo       Instagram Bot - Fast Update Tool
echo ==================================================
echo.

:: 1. Try running updater.py with Virtual Environment Python
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" "%~dp0updater.py"
    goto DONE
)

:: 2. Try running updater.py with System Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    python "%~dp0updater.py"
    goto DONE
)

:: 3. Fallback to PowerShell script
echo Python was not found in PATH. Using PowerShell updater...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_fallback.ps1"

:DONE
echo.
pause
