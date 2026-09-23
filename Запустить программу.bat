@echo off
setlocal
cd /d "%~dp0"
set "APP_FILE=%~dp0app.py"

if not exist "%APP_FILE%" (
  echo The application file was not found: "%APP_FILE%"
  pause
  exit /b 1
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
  start "" /D "%~dp0" pyw.exe -3 -B "%APP_FILE%"
  exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
  start "" /D "%~dp0" pythonw.exe -B "%APP_FILE%"
  exit /b 0
)

echo Python was not found. Install Python 3 and run this file again.
pause
