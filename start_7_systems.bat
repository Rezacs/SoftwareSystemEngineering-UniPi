@echo off
setlocal

REM Root = folder where this BAT file is
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

REM Go 2 folders back from BAT location, then venv\Scripts\activate.bat
for %%I in ("%ROOT%\..\..\venv\Scripts\activate.bat") do set "VENV_ACTIVATE=%%~fI"

echo.
set /p USE_VENV=Do you want to activate the virtual environment-TYPE N? (Y/N): 
echo.

if /I "%USE_VENV%"=="Y" goto WITH_VENV
goto WITHOUT_VENV

:WITH_VENV
start "Client Side System" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\client_side" && python main.py"
timeout /t 2 >nul

start "Ingestion Launcher" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python ingestion_launcher.py"
timeout /t 2 >nul

start "Preparation Launcher" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python preparation_launcher.py"
timeout /t 2 >nul

start "Segregation System" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\segregation" && python main.py"
timeout /t 2 >nul

start "Development System" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\development" && python main.py"
timeout /t 2 >nul

start "Production System" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\production" && python main.py"
timeout /t 2 >nul

start "Evaluation System" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\evaluation" && python -m src.main"
goto END

:WITHOUT_VENV
start "Client Side System" cmd /k "cd /d "%ROOT%\client_side" && python main.py"
timeout /t 2 >nul

start "Ingestion Launcher" cmd /k "cd /d "%ROOT%" && python ingestion_launcher.py"
timeout /t 2 >nul

start "Preparation Launcher" cmd /k "cd /d "%ROOT%" && python preparation_launcher.py"
timeout /t 2 >nul

start "Ingestion System" cmd /k "cd /d "%ROOT%\ingestion" && python ingestion_launcher.py"
timeout /t 2 >nul

start "Development System" cmd /k "cd /d "%ROOT%\development" && python main.py"
timeout /t 2 >nul

start "Production System" cmd /k "cd /d "%ROOT%\production" && python main.py"
timeout /t 2 >nul

start "Evaluation System" cmd /k "cd /d "%ROOT%\evaluation\src" && python main.py"
goto END

:END
endlocal