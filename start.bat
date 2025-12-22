@echo off
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║   ███╗   ██╗███████╗██╗  ██╗ ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
echo ║   ████╗  ██║██╔════╝╚██╗██╔╝██╔═══██╗██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
echo ║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████║██║   ██║███████╗   ██║   
echo ║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║██╔══██║██║   ██║╚════██║   ██║   
echo ║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   
echo ║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   
echo ║                                                               ║
echo ║                    Nexo-VM-Panel                              ║
echo ║              Welcome to NexoHost! Power Your Future!          ║
echo ║                                                               ║
echo ║   Starting server...                                          ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

REM Start the application
echo [INFO] Starting Nexo-VM-Panel...
echo.
python nexovm.py

pause
