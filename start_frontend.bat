@echo off
title Udyam Saathi — Web Frontend (Port 3000)
echo ====================================================================
echo Starting Udyam Saathi Web Frontend on http://127.0.0.1:3000 ...
echo ====================================================================
python -m http.server 3000 --directory frontend
pause
