@echo off
chcp 65001 >nul
title NPL Portfolio Platform
echo.
echo  ================================
echo   NPL Portfolio Platform
echo  ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python not found. Install from https://python.org
    pause
    exit /b
)

:: Install dependencies
echo  Installing dependencies...
pip install flask openpyxl --quiet 2>nul

:: Start server
echo.
echo  Starting server...
echo  Open in browser: http://localhost:5000
echo.
echo  Press Ctrl+C to stop
echo.
start http://localhost:5000
python scripts\webapp.py
pause
