@echo off
chcp 65001 >nul
cd /d %~dp0

set PORT=8000
set HOME_URL=http://localhost:%PORT%/
set EN_URL=http://localhost:%PORT%/index-en.html
set ADMIN_URL=http://localhost:%PORT%/admin/index.html

echo.
echo ========================================
echo  Long March Spark Routes - Local Server
echo ========================================
echo.
echo  Chinese home page:
echo  %HOME_URL%
echo.
echo  English page:
echo  %EN_URL%
echo.
echo  Admin panel:
echo  %ADMIN_URL%
echo.
echo  Your browser will open the Chinese home page automatically.
echo  If it does not open, copy one of the links above into your browser.
echo  Keep this window open while using the project.
echo  Close this window to stop the local server.
echo.

start "" "%HOME_URL%"
python -m http.server %PORT%
if errorlevel 1 (
  echo.
  echo Python command failed. Trying the Windows py launcher...
  py -m http.server %PORT%
)
pause
