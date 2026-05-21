@echo off
chcp 65001 >nul
cd /d %~dp0\..

if "%~1"=="" (
  echo Usage:
  echo   tools\extract_steam_texts.bat "D:\SteamLibrary\steamapps\common\Long March 1934-1936"
  echo.
  echo Optional:
  echo   python tools\extract_steam_texts.py --game-keyword "Long March" --include-binary
  pause
  exit /b 2
)

python tools\extract_steam_texts.py %*
if errorlevel 1 (
  echo.
  echo Python command failed. Trying the Windows py launcher...
  py tools\extract_steam_texts.py %*
)
pause
