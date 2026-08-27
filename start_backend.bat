@echo off
title Udyam Saathi — FastAPI Backend (Port 8000)
cd /d "%~dp0"
set PYTHONPATH=%cd%;%cd%\backend
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo ====================================================================
echo Starting Udyam Saathi REST API Backend on http://127.0.0.1:8000 ...
echo ====================================================================
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause

