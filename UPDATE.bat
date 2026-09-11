@echo off
setlocal enabledelayedexpansion
title Instagram Bot - Fast Updater
color 0B

echo ==================================================
echo       Instagram Bot - Fast Update Tool
echo ==================================================
echo.

:: 1. Check if Git repository is configured in this folder
if exist "%~dp0.git" (
    echo [1/3] Git repository detected! Pulling latest code...
    git pull
    if not errorlevel 1 (
        echo.
        echo [SUCCESS] Pulled latest updates from Git!
        goto AFTER_UPDATE
    ) else (
        echo [INFO] Git pull encountered an error, checking other update sources...
    )
)

:: 2. Check if user configured a GitHub repository URL in .github_repo
if exist "%~dp0.github_repo" (
    set /p REPO_URL=<"%~dp0.github_repo"
    if not "!REPO_URL!"=="" (
        echo [1/3] Downloading latest scripts directly from GitHub (!REPO_URL!)...
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "$repo = (Get-Content '%~dp0.github_repo').Trim(); ^
            $files = @('main.py', 'ldplayer_automation.py', 'easyearn_client.py', 'requirements.txt', 'run.bat', 'UPDATE.bat'); ^
            foreach ($f in $files) { ^
                $rawUrl = $repo.Replace('github.com', 'raw.githubusercontent.com') + '/main/' + $f; ^
                try { ^
                    Invoke-WebRequest -Uri $rawUrl -OutFile ('%~dp0' + $f) -UseBasicParsing; ^
                    Write-Host ('   Updated: ' + $f) -ForegroundColor Green; ^
                } catch { ^
                    $rawUrlMaster = $repo.Replace('github.com', 'raw.githubusercontent.com') + '/master/' + $f; ^
                    try { ^
                        Invoke-WebRequest -Uri $rawUrlMaster -OutFile ('%~dp0' + $f) -UseBasicParsing; ^
                        Write-Host ('   Updated: ' + $f) -ForegroundColor Green; ^
                    } catch { ^
                        Write-Host ('   Skipped / not found: ' + $f) -ForegroundColor Yellow; ^
                    } ^
                } ^
            }"
        goto AFTER_UPDATE
    )
)

:: 3. Check for any newly downloaded ZIP in Downloads folder or current folder
echo [1/3] Checking for exported ZIP files in Downloads...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$downloadDir = [Environment]::GetFolderPath('UserProfile') + '\Downloads'; ^
    $zips = Get-ChildItem -Path $downloadDir\*.zip, '%~dp0*.zip' -ErrorAction SilentlyContinue | ^
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) -or $_.Name -match 'c7cb1f|Instagram|react' } | ^
            Sort-Object LastWriteTime -Descending; ^
    if ($zips.Count -gt 0) { ^
        $latest = $zips[0]; ^
        Write-Host ('Found recent export ZIP: ' + $latest.FullName) -ForegroundColor Cyan; ^
        $tempDir = Join-Path $env:TEMP ('bot_update_' + [System.Guid]::NewGuid().ToString('N').Substring(0,8)); ^
        Expand-Archive -Path $latest.FullName -DestinationPath $tempDir -Force; ^
        $count = 0; ^
        Get-ChildItem -Path $tempDir -Recurse -File | Where-Object { $_.Extension -in @('.py', '.bat', '.txt', '.json') } | ForEach-Object { ^
            Copy-Item -Path $_.FullName -Destination '%~dp0' -Force; ^
            $count++; ^
        }; ^
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue; ^
        Write-Host ('Successfully updated ' + $count + ' files into your bot folder!') -ForegroundColor Green; ^
        exit 0; ^
    } else { ^
        Write-Host 'No recent export ZIP found in Downloads.' -ForegroundColor Yellow; ^
        exit 1; ^
    }"

if errorlevel 1 (
    echo.
    echo ==================================================
    echo              CHOOSE AN UPDATE METHOD
    echo ==================================================
    echo Option 1: Zero-Click Sync via GitHub (RECOMMENDED)
    echo   1. In AI Studio, click top-right menu -> 'Export to GitHub'.
    echo   2. Paste your repository URL below:
    set /p NEW_REPO="GitHub Repo URL (e.g. https://github.com/username/instagram-bot, or press Enter): "
    if not "!NEW_REPO!"=="" (
        echo !NEW_REPO!> "%~dp0.github_repo"
        echo Saved repository URL! Running update now...
        "%~dp0UPDATE.bat"
        exit /b
    )
    echo.
    echo Option 2: 1-Click Export ZIP
    echo   Just click 'Export to ZIP' in AI Studio. When the download finishes,
    echo   run UPDATE.bat. It will automatically detect the ZIP in your Downloads
    echo   folder, extract all python files, and update them automatically!
    echo.
    pause
    exit /b
)

:AFTER_UPDATE
echo.
echo [2/3] Checking dependencies...
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt" --quiet
) else (
    pip install -r "%~dp0requirements.txt" --quiet
)

echo.
echo [3/3] Update completed successfully!
echo.
echo TIP: You do NOT need to re-compile Instagram_Bot.exe every time.
echo You can run "run.bat" to start the updated bot immediately!
echo.
set /p REBUILD="Do you want to re-compile to Instagram_Bot.exe anyway? (y/N): "
if /i "!REBUILD!"=="y" (
    echo Compiling to Instagram_Bot.exe...
    if exist "%~dp0venv\Scripts\pyinstaller.exe" (
        "%~dp0venv\Scripts\pyinstaller.exe" --noconsole --onefile --name "Instagram_Bot" --collect-all selenium --collect-all webdriver_manager main.py
        move /y dist\Instagram_Bot.exe "%~dp0Instagram_Bot.exe" >nul 2>&1
        rmdir /s /q build >nul 2>&1
        rmdir /s /q dist >nul 2>&1
        del /q Instagram_Bot.spec >nul 2>&1
        echo Successfully recompiled Instagram_Bot.exe!
    ) else (
        pyinstaller --noconsole --onefile --name "Instagram_Bot" --collect-all selenium --collect-all webdriver_manager main.py
        move /y dist\Instagram_Bot.exe "%~dp0Instagram_Bot.exe" >nul 2>&1
        rmdir /s /q build >nul 2>&1
        rmdir /s /q dist >nul 2>&1
        del /q Instagram_Bot.spec >nul 2>&1
        echo Successfully recompiled Instagram_Bot.exe!
    )
) else (
    echo Skipped compilation.
)

echo.
echo ==================================================
echo                  ALL DONE!
echo ==================================================
echo You can double-click "run.bat" to start right now.
echo.
pause
