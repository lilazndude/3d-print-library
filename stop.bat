@echo off
echo.
echo  Stopping 3D Print Library...

taskkill /FI "WINDOWTITLE eq 3D Print Library" /T /F >nul 2>&1
if %errorlevel% equ 0 (
    echo  Server stopped.
) else (
    echo  Server was not running.
)

echo.
timeout /t 2 /nobreak >nul
