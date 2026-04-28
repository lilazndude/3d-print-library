@echo off
title 3D Print Library - Installer

set "SCRIPTDIR=%~dp0"
set PUSHED=0
if "%SCRIPTDIR:~0,2%"=="\\" (
    pushd "%~dp0"
    set PUSHED=1
) else (
    cd /d "%~dp0"
)

echo.
echo  3D Print Library - First-Time Setup
echo  =====================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo.
    echo  Please install Python 3.8 or newer from https://python.org
    echo  During installation, check "Add Python to PATH".
    echo.
    goto :fail
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Found Python %PYVER%
echo.

:: ── Create virtual environment (venv_win to avoid conflict with Linux venv) -
if exist "_app\venv_win\Scripts\python.exe" (
    echo  Virtual environment already exists. Re-installing dependencies...
) else (
    echo  Creating virtual environment...
    python -m venv _app\venv_win
    if errorlevel 1 (
        echo.
        echo  ERROR: Could not create virtual environment.
        goto :fail
    )
)
echo.

:: ── Install dependencies ───────────────────────────────────────────────────
echo  Installing dependencies - this may take a few minutes...
echo  (Flask, Trimesh, NumPy, Matplotlib, SciPy, NetworkX)
echo.
_app\venv_win\Scripts\pip install --upgrade pip -q
_app\venv_win\Scripts\pip install -r _app\requirements.txt
if errorlevel 1 (
    echo.
    echo  ERROR: Dependency installation failed.
    echo  Check your internet connection and try again.
    goto :fail
)

echo.
echo  =====================================
echo   Setup complete!
echo   Double-click run.bat to launch.
echo  =====================================
echo.
goto :done

:fail
if "%PUSHED%"=="1" popd
pause
exit /b 1

:done
if "%PUSHED%"=="1" popd
pause
