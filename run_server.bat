@echo off
title VeriClaim AI - Multi-Lingual Fact Verification System
echo ================================================================
echo           VeriClaim AI - Starting Server...
echo ================================================================
cd /d "%~dp0"
if exist ".python311\python.exe" (
    start http://127.0.0.1:8000
    ".python311\python.exe" backend\app.py
) else (
    start http://127.0.0.1:8000
    python backend\app.py
)
pause
