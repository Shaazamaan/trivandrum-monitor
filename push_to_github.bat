@echo off
echo ========================================================
echo       GOOGLE MAPS MONITOR - GITHUB UPLOADER (FIXED)
echo ========================================================
echo.
echo Target: https://github.com/Shaazamaan/trivandrum-monitor.git
echo.

echo Configuring remote...
git remote remove origin 2>nul
git remote add origin https://github.com/Shaazamaan/trivandrum-monitor.git

echo.
echo Pushing code to GitHub (FORCE OVERWRITE)...
echo This will fix the "fetch first" error by overwriting the remote.
echo.
git branch -M main
git push -u origin main --force

echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo SUCCESS! The monitor is now installed on GitHub.
    echo Go to https://github.com/Shaazamaan/trivandrum-monitor/actions
    echo to see it running!
) else (
    echo FAILED. Please check provided credentials.
)
echo ========================================================
pause
