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

echo Cleaning previous data files...
if exist "%ROOT%\development\Data\reports\*.*"    del /q "%ROOT%\development\Data\reports\*.*"
if exist "%ROOT%\development\Data\classifiers\*.*" del /q "%ROOT%\development\Data\classifiers\*.*"
if exist "%ROOT%\evaluation\output\*.*"            del /q "%ROOT%\evaluation\output\*.*"
if exist "%ROOT%\evaluation\data\*.db"             del /q "%ROOT%\evaluation\data\*.db"
if exist "%ROOT%\segregation\data\output\*.*"      del /q "%ROOT%\segregation\data\output\*.*"
if exist "%ROOT%\segregation\data\input\*.db"      del /q "%ROOT%\segregation\data\input\*.db"
echo Data cleaned.

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
wt -w 0 nt --title "Client Side"  cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\client_side" && python main.py" ^
   ; nt --title "Ingestion"        cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python -m ingestion.main" ^
   ; nt --title "Preparation"      cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%" && python -m preparation.main" ^
   ; nt --title "Segregation"      cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\segregation" && python main.py" ^
   ; nt --title "Development"      cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\development" && python main.py" ^
   ; nt --title "Production"       cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\production" && python main.py" ^
   ; nt --title "Evaluation"       cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\evaluation" && python -m src.main"


wt -w 1 nt --title "Ingestion"    cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\ingestion"" ^
   ; nt --title "Preparation"      cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\preparation"" ^
   ; nt --title "Production"       cmd /k "call "%VENV_ACTIVATE%" && cd /d "%ROOT%\production"" ^
goto END

:WITHOUT_VENV
wt -w 0 nt --title "Client Side"  cmd /k "cd /d "%ROOT%\client_side" && python main.py" ^
   ; nt --title "Ingestion"        cmd /k "cd /d "%ROOT%" && python -m ingestion.main" ^
   ; nt --title "Preparation"      cmd /k "cd /d "%ROOT%" && python -m preparation.main" ^
   ; nt --title "Segregation"      cmd /k "cd /d "%ROOT%\segregation" && python main.py" ^
   ; nt --title "Development"      cmd /k "cd /d "%ROOT%\development" && python main.py" ^
   ; nt --title "Production"       cmd /k "cd /d "%ROOT%\production" && python main.py" ^
   ; nt --title "Evaluation"       cmd /k "cd /d "%ROOT%\evaluation" && python -m src.main"

wt -w 1 nt --title "Ingestion"    cmd /k "cd /d "%ROOT%\ingestion"" ^
   ; nt --title "Preparation"      cmd /k "cd /d "%ROOT%\preparation"" ^
   ; nt --title "Production"       cmd /k "cd /d "%ROOT%\production"" ^

goto END

:END
endlocal