@echo off
chcp 65001 >nul 2>&1
title Meeting System - Server
cd /d "%~dp0"

echo ========================================
echo   会议室预约系统 - 服务端
echo ========================================
echo.

py server.py

pause
