@echo off
setlocal
cd /d "%~dp0\.."
python tools\check_project.py
exit /b %ERRORLEVEL%
