@echo off
setlocal

cd /d "%~dp0"

set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

call "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" "%~dp0desktop_gui.py"

exit /b %errorlevel%