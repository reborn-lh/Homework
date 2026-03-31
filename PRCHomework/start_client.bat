@echo off
chcp 65001 >nul 2>&1
title Meeting System - Client
cd /d "%~dp0"

echo ========================================
echo   会议室预约系统 - 客户端
echo ========================================
echo.

py client.py

pause
