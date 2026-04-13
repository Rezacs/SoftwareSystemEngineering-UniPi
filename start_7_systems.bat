@echo off
setlocal

REM Root = folder where this BAT file is
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

REM Go 2 folders back from BAT location, then venv\Scripts\activate.bat
for %%I in ("%ROOT%\..\..\venv\Scripts\activate.bat") do set "VENV_ACTIVATE=%%~fI"

echo.
set /p USE_VENV=Do you want to activate the virtual environment? (Y/N): 
echo.

echo Cleaning previous log files...
if exist "%ROOT%\logs\*.json" del /q "%ROOT%\logs\*.json"
echo Logs cleaned.

@REM set /p DEV_MODE=Development mode? (1=Stop and Go, 2=Testing): 
@REM set /p SEG_MODE=Segregation mode? (1=Stop and Go, 2=Testing): 
@REM set /p EVAL_MODE=Evaluation mode? (1=Stop and Go, 2=Testing): 

@REM set "GENERAL_CONFIG=%ROOT%\config\GeneralConfig.json"

@REM powershell -NoProfile -Command ^
@REM   "$p = '%GENERAL_CONFIG%';" ^
@REM   "$j = Get-Content $p -Raw | ConvertFrom-Json;" ^
@REM   "if (-not $j.development) { $j | Add-Member -MemberType NoteProperty -Name development -Value (@{}) }" ^
@REM   "if (-not $j.segregation) { $j | Add-Member -MemberType NoteProperty -Name segregation -Value (@{}) }" ^
@REM   "if (-not $j.evaluation) { $j | Add-Member -MemberType NoteProperty -Name evaluation -Value (@{}) }" ^
@REM   "$j.development | Add-Member -Force -MemberType NoteProperty -Name mode -Value '%DEV_MODE%';" ^
@REM   "$j.segregation | Add-Member -Force -MemberType NoteProperty -Name mode -Value '%SEG_MODE%';" ^
@REM   "$j.evaluation | Add-Member -Force -MemberType NoteProperty -Name mode -Value '%EVAL_MODE%';" ^
@REM   "$j | ConvertTo-Json -Depth 10 | Set-Content $p"

if /I "%USE_VENV%"=="Y" goto WITH_VENV
goto WITHOUT_VENV

:WITH_VENV
:: Start the first tab (this creates the window)
wt -w 0 nt --title "Client Side" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\client_side" && python main.py"

:: Add subsequent tabs to the same window (-w 0)
wt -w 0 nt --title "Ingestion" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python -m ingestion.main"
wt -w 0 nt --title "Preparation" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python -m preparation.main"
wt -w 0 nt --title "Segregation" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\segregation" && python main.py"
wt -w 0 nt --title "Development" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\development" && python main.py"
wt -w 0 nt --title "Production" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\production" && python main.py"
wt -w 0 nt --title "Evaluation" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\evaluation" && python -m src.main"
goto END

:WITHOUT_VENV
wt -w 0 nt --title "Client Side" cmd /k "cd /d "%ROOT%\client_side" && python main.py"
wt -w 0 nt --title "Ingestion Launcher" cmd /k "cd /d "%ROOT%" && python -m ingestion.main"
wt -w 0 nt --title "Preparation Launcher" cmd /k "cd /d "%ROOT%" && python -m preparation.main"
wt -w 0 nt --title "Ingestion System" cmd /k "cd /d "%ROOT%\ingestion" && python ingestion_launcher.py"
wt -w 0 nt --title "Development System" cmd /k "cd /d "%ROOT%\development" && python main.py"
wt -w 0 nt --title "Production System" cmd /k "cd /d "%ROOT%\production" && python main.py"
wt -w 0 nt --title "Evaluation System" cmd /k "cd /d "%ROOT%\evaluation\src" && python main.py"
goto END

:END
endlocal