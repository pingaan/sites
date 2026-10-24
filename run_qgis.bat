@echo off
setlocal
cd /d "%~dp0"

set "PATH=%SystemRoot%\System32;%SystemRoot%\System32\WindowsPowerShell\v1.0;%SystemRoot%\System32\OpenSSH;%PATH%"

set "PYTHONUNBUFFERED=1"
set "SITES_DATABASE_ENV=%LOCALAPPDATA%\Sites\database.env"

if not exist "%SITES_DATABASE_ENV%" (
    echo ERROR: Database configuration file is missing:
    echo %SITES_DATABASE_ENV%
    exit /b 1
)

for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%SITES_DATABASE_ENV%") do (
    if not "%%A"=="" set "%%A=%%B"
)

if not defined SITES_DB_HOST (
    echo ERROR: SITES_DB_HOST is missing from:
    echo %SITES_DATABASE_ENV%
    exit /b 1
)

if not defined SITES_DB_PASSWORD (
    echo ERROR: SITES_DB_PASSWORD is missing from:
    echo %SITES_DATABASE_ENV%
    exit /b 1
)

"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_sites_tunnel.ps1"

if errorlevel 1 (
    echo ERROR: Could not establish the Sites database tunnel.
    exit /b 1
)

call "C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat" -X faulthandler -c "import os, sys, runpy; sys.path.insert(0, os.path.join(os.environ['QGIS_PREFIX_PATH'], 'python', 'plugins')); runpy.run_path(sys.argv[1], run_name='__main__')" "%~dp0main.py"

exit /b %errorlevel%