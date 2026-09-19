@echo off
setlocal
cd /d "%~dp0"

set "PYTHONUNBUFFERED=1"

call "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" -X faulthandler -c "import os, sys, runpy; sys.path.insert(0, os.path.join(os.environ['QGIS_PREFIX_PATH'], 'python', 'plugins')); runpy.run_path(sys.argv[1], run_name='__main__')" "%~dp0main.py"

exit /b %errorlevel%