@echo off
cd /d "%~dp0\.."
python tools\build_json_from_tables.py
pause
