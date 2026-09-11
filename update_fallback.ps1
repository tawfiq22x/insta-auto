# update_fallback.ps1
$dir = $PSScriptRoot
Write-Host "Checking for .github_repo or Downloads ZIP..." -ForegroundColor Cyan

if (Test-Path "$dir\.github_repo") {
    $repo = (Get-Content "$dir\.github_repo").Trim()
    if ($repo) {
        Write-Host "Downloading from GitHub: $repo" -ForegroundColor Green
        $files = @('main.py', 'ldplayer_automation.py', 'easyearn_client.py', 'requirements.txt', 'run.bat', 'UPDATE.bat', 'updater.py')
        foreach ($f in $files) {
            $rawUrl = $repo.Replace('github.com', 'raw.githubusercontent.com') + '/main/' + $f
            try {
                Invoke-WebRequest -Uri $rawUrl -OutFile "$dir\$f" -UseBasicParsing
                Write-Host "  Updated: $f" -ForegroundColor Green
            } catch {
                Write-Host "  Skipped: $f" -ForegroundColor Yellow
            }
        }
        exit 0
    }
}

$downloadDir = [Environment]::GetFolderPath('UserProfile') + '\Downloads'
$zips = Get-ChildItem -Path "$downloadDir\*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($zips.Count -gt 0) {
    $latest = $zips[0]
    Write-Host "Found recent ZIP: $($latest.FullName)" -ForegroundColor Cyan
    $tempDir = Join-Path $env:TEMP ('bot_update_' + [System.Guid]::NewGuid().ToString('N').Substring(0,8))
    Expand-Archive -Path $latest.FullName -DestinationPath $tempDir -Force
    Get-ChildItem -Path $tempDir -Recurse -File | Where-Object { $_.Extension -in @('.py', '.bat', '.txt') } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $dir -Force
        Write-Host "  Updated: $($_.Name)" -ForegroundColor Green
    }
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Update from ZIP complete!" -ForegroundColor Green
}
