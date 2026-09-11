@echo off
title Building Windows Executable...
color 0B

echo ========================================
echo   Building Standalone Windows App
echo ========================================
echo.
echo Installing PyInstaller and dependencies...
pip install -r requirements.txt pyinstaller --quiet

echo.
echo Compiling the application (this may take a minute)...
pyinstaller --noconsole --onefile --name "Instagram_Automation_Suite" main.py

echo.
echo ========================================
echo ✅ BUILD COMPLETE!
echo ========================================
echo Your standalone application is ready.
echo Open the "dist" folder to find "Instagram_Automation_Suite.exe".
echo You can move this .exe file anywhere on your PC and double-click it to run!
echo.
pause
