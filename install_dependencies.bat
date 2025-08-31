@echo off
TITLE Project Setup

ECHO ===================================================
ECHO  Starting Full Project Setup (Backend & Frontend)
ECHO ===================================================
ECHO.

REM --- Step 1: Install Python Dependencies ---
ECHO [1/2] Installing Python backend dependencies...
ECHO --------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    ECHO ERROR: Python is not installed or not in your PATH.
    ECHO Please install Python 3 and try again.
    GOTO:FAIL
)
pip install -r requirements.txt
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to install Python packages. See errors above.
    GOTO:FAIL
)
ECHO Python dependencies installed successfully.
ECHO.

REM --- Step 2: Install Node.js Dependencies ---
ECHO [2/2] Installing Node.js frontend dependencies...
ECHO --------------------------------------------
node --version >nul 2>&1
if %errorlevel% neq 0 (
    ECHO ERROR: Node.js is not installed or not in your PATH.
    ECHO Please install Node.js (which includes npm) and try again.
    GOTO:FAIL
)

REM Assumes the frontend code is in a 'frontend' directory
REM next to your 'backend' directory.
IF NOT EXIST ".\webserver\frontend\package.json" (
    ECHO ERROR: Could not find 'package.json' in the 'webserver\frontend' directory.
    ECHO Please ensure your React app is located there.
    GOTO:FAIL
)
cd webserver\frontend
npm install
if %errorlevel% neq 0 (
    ECHO ERROR: Failed to install Node.js packages. See errors above.
    cd ..\..
    GOTO:FAIL
)
cd ..\..
ECHO Node.js dependencies installed successfully.
ECHO.

ECHO ===================================================
ECHO  Project setup completed successfully!
ECHO ===================================================
ECHO.
GOTO:END

:FAIL
ECHO.
ECHO ---------------------------------------------------
ECHO  Setup failed. Please review the error messages.
ECHO ---------------------------------------------------
ECHO.

:END
pause
