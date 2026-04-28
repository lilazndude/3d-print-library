@echo off
pushd "%~dp0"
where python >nul 2>&1 || (echo Python not found. Install from python.org & pause & exit /b 1)
python -m pip show flask >nul 2>&1 || python -m pip install flask
python app.py
pause
