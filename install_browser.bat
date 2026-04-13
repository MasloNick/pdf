@echo off
chcp 65001 >nul
title NPL Platform — Install Browser Engine
echo.
echo  ==========================================
echo   Встановлення браузерного движка (Chromium)
echo  ==========================================
echo.
echo  Це потрібно один раз для глибокого сканування
echo  сайтів SETAM, ProZorro, банків...
echo.
pip install playwright
playwright install chromium
echo.
echo  ==========================================
echo   Готово! Тепер глибоке сканування працює.
echo  ==========================================
pause
