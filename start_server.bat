@echo off
chcp 65001 >nul
cd /d %~dp0

set PORT=8000
set EXPLORE_URL=http://localhost:%PORT%/explore.html
set MUSEUM_URL=http://localhost:%PORT%/museum.html
set HOME_URL=http://localhost:%PORT%/
set MAP_URL=http://localhost:%PORT%/map.html
set EN_URL=http://localhost:%PORT%/index-en.html
set ADMIN_URL=http://localhost:%PORT%/admin/index.html

echo.
echo ========================================
echo  Long March Spark Routes - Local Server
echo ========================================
echo.
echo  Thematic entry (recommended):
echo  %EXPLORE_URL%
echo.
echo  Digital museum:
echo  %MUSEUM_URL%
echo.
echo  Chinese home page:
echo  %HOME_URL%
echo.
echo  Route map:
echo  %MAP_URL%
echo.
echo  English page:
echo  %EN_URL%
echo.
echo  Admin panel:
echo  %ADMIN_URL%
echo.
echo  Your browser will open the thematic entry page automatically.
echo  If it does not open, copy one of the links above into your browser.
echo  Keep this window open while using the project.
echo  Close this window to stop the local server.
echo.

start "" "%EXPLORE_URL%"
python -m http.server %PORT%
if errorlevel 1 (
  echo.
  echo Python command failed. Trying the Windows py launcher...
  py -m http.server %PORT%
)
pause
