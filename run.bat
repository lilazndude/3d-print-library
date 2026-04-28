@echo off
title 3D Print Library

set "SCRIPTDIR=%~dp0"
set PUSHED=0
if "%SCRIPTDIR:~0,2%"=="\\" (
    pushd "%~dp0"
    set PUSHED=1
) else (
    cd /d "%~dp0"
)

if not exist "_app\venv_win\Scripts\python.exe" (
    echo.
    echo  Virtual environment not found.
    echo  Please run install.bat first.
    echo.
    pause
    goto :done
)

echo.
echo  Starting 3D Print Library...
echo  The site will open in your browser shortly.
echo.
echo  A tray icon will appear in your system tray.
echo  You can minimize this window - closing it will stop the server.
echo.

_app\venv_win\Scripts\python.exe _app\app.py

:done
if "%PUSHED%"=="1" popd
