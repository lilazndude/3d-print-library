@echo off
setlocal

set "REPODIR=%~dp0"
if "%REPODIR:~-1%"=="\" set "REPODIR=%REPODIR:~0,-1%"

echo.
echo  3D Print Library - Create Desktop Shortcut
echo  ============================================
echo.

powershell -NoProfile -Command "$d=[Environment]::GetFolderPath('Desktop'); $repo='%REPODIR%'; $ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut($d+'\3D Print Library.lnk'); $s.TargetPath='C:\Windows\System32\wscript.exe'; $s.Arguments='\"'+$repo+'\launch.vbs\"'; $s.WindowStyle=1; $s.Save()"

echo  Shortcut created on your Desktop.
echo  - First click: starts the server (splash appears, then tray icon)
echo  - Subsequent clicks: opens the site directly
echo.
pause
