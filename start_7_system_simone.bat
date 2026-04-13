@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo Cleaning previous log files...
if exist "%ROOT%\logs\*.json" del /q "%ROOT%\logs\*.json"

:: Launching all systems in separate windows
start "Client Side" cmd /k "cd /d "%ROOT%\client_side" && python main.py"
start "Ingestion" cmd /k "cd /d "%ROOT%" && python ingestion_launcher.py"
start "Preparation" cmd /k "cd /d "%ROOT%" && python preparation_launcher.py"
start "Ingestion System" cmd /k "cd /d "%ROOT%\ingestion" && python ingestion_launcher.py"
start "Development" cmd /k "cd /d "%ROOT%\development" && python main.py"
start "Production" cmd /k "cd /d "%ROOT%\production" && python main.py"
start "Evaluation" cmd /k "cd /d "%ROOT%\evaluation\src" && python main.py"

endlocal