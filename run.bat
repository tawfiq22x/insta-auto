@echo off
title Instagram Automation Suite
color 0A

echo ========================================
echo   Instagram Automation Suite
echo ========================================
echo.

REM Check Python / Venv
if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in PATH!
        echo Please run INSTALL.bat first.
        pause
        exit /b
    )
    set "PYTHON_CMD=python"
)

REM Run the app immediately
echo Starting automation suite...
%PYTHON_CMD% main.py

pause
