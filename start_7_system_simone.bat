@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo Cleaning previous log files...
if exist "%ROOT%\logs\*.json" del /q "%ROOT%\logs\*.json"

wt ^
new-tab --title "Client Side" cmd /k "cd /d "%ROOT%\client_side" && python main.py" ; ^
new-tab --title "Ingestion" cmd /k "cd /d "%ROOT%" && python -m ingestion.main" ; ^
new-tab --title "Preparation" cmd /k "cd /d "%ROOT%" && python -m preparation.main" ; ^
new-tab --title "Segregation" cmd /k "cd /d "%ROOT%\ingestion" && python main.py" ; ^
new-tab --title "Development" cmd /k "cd /d "%ROOT%\development" && python main.py" ; ^
new-tab --title "Production" cmd /k "cd /d "%ROOT%\production" && python main.py" ; ^
new-tab --title "Evaluation" cmd /k "cd /d "%ROOT%\evaluation\src" && python -m src.main"

endlocal