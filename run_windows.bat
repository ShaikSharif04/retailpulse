@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo Starting RetailPulse
 echo ============================================
if not exist .venv\Scripts\python.exe (
    echo Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 goto error
)
echo Installing required packages...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo Launching RetailPulse in your browser...
.venv\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 goto error
goto end
:error
echo.
echo Setup or launch failed. Read the error message above.
pause
:end
endlocal
