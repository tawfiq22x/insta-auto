@echo off
title Installing Instagram Automation Suite...
color 0B

echo ==================================================
echo   Instagram Automation Suite - 1-Click Installer
echo ==================================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/downloads/
    echo VERY IMPORTANT: Check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit
)

:: 2. Create a clean virtual environment
echo [1/3] Creating isolated Python environment...
python -m venv venv

:: 3. Install required packages
echo.
echo [2/3] Installing dependencies (this may take a moment)...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
venv\Scripts\python.exe -m pip install pyinstaller --quiet

:: 4. Build the executable
echo.
echo [3/3] Compiling to a standalone executable...
venv\Scripts\pyinstaller.exe --noconsole --onefile --name "Instagram_Bot" --collect-all selenium --collect-all webdriver_manager main.py

:: 5. Cleanup and move
echo.
echo Cleaning up build files...
move dist\Instagram_Bot.exe "%~dp0Instagram_Bot.exe" >nul
rmdir /s /q build
rmdir /s /q dist
del /q Instagram_Bot.spec

echo.
echo ==================================================
echo                      SUCCESS!
echo ==================================================
echo.
echo The installation is completely finished.
echo.
echo You will now see a file named "Instagram_Bot.exe" in this folder.
echo You can double-click it to run the application immediately.
echo You can also move "Instagram_Bot.exe" to your Desktop for easy access!
echo.
pause
