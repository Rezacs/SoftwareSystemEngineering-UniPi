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
start "Client Side System" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\client_side" && python main.py"
timeout /t 2 >nul

start "Ingestion Launcher" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python -m ingestion.main"
timeout /t 2 >nul

start "Preparation Launcher" cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python -m preparation.main"
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