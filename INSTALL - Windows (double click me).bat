@echo off
setlocal EnableDelayedExpansion
title Video Processor - Auto Setup
color 0B
cls

echo.
echo   ╔══════════════════════════════════════════════════╗
echo   ║   🎬 Video Processor — Auto Setup               ║
echo   ║   mediversebd.com                               ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo   Installing everything needed and launching the app.
echo   You only need to do this once.
echo.

:: ── Check Windows version (need Win 10/11 for winget) ──────
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo   Windows version detected.

:: ── Step 1: Check / Install Python ─────────────────────────
echo   [1/2] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [1/2] Installing Python via winget...
    winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo.
        echo   ⚠️  Automatic install failed. Opening Python download page...
        echo   Please download and install Python manually.
        echo   IMPORTANT: Check "Add Python to PATH" during install!
        echo.
        start https://www.python.org/downloads/
        pause
        exit /b
    )
    :: Refresh PATH
    call refreshenv >nul 2>&1
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts"
)
echo   [1/2] ✅ Python: OK

:: ── Step 2: Check / Install FFmpeg ─────────────────────────
echo   [2/2] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   [2/2] Installing FFmpeg via winget...
    winget install -e --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo.
        echo   ⚠️  Automatic install failed. Opening FFmpeg download page...
        start https://www.gyan.dev/ffmpeg/builds/
        echo.
        echo   Download ffmpeg-release-essentials.zip
        echo   Extract to C:\ffmpeg
        echo   Add C:\ffmpeg\bin to your Windows PATH
        echo.
        pause
        exit /b
    )
    :: Refresh PATH for FFmpeg
    set "PATH=%PATH%;C:\ffmpeg\bin;%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-6.0-essentials_build\bin"
)
echo   [2/2] ✅ FFmpeg: OK

:: ── Launch App ──────────────────────────────────────────────
echo.
echo   ╔══════════════════════════════════════════════════╗
echo   ║   ✅ All set! Launching the app...              ║
echo   ╚══════════════════════════════════════════════════╝
echo.
echo   Your browser will open automatically.
echo   Keep this window open while using the app.
echo.

python "%~dp0video_processor_app.py"
pause
