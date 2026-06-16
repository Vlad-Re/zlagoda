@echo off
title Zlagoda Frontend
cd /d "%~dp0frontend"

echo [1/2] Installing frontend dependencies...
call npm install

echo [2/2] Starting Vite development server...
call npm run dev
pause