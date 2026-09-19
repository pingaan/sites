@echo off
setlocal
cd /d "%~dp0"

set "PYTHONPATH=C:\Program Files\QGIS 3.44.14\apps\qgis-ltr\python\plugins"
set "PYTHONUNBUFFERED=1"

call "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" -X faulthandler "%~dp0main.py"

exit /b %errorlevel%