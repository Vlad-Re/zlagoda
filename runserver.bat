@echo off
title Zlagoda Backend
cd /d "%~dp0backend"

echo [1/4] Running database migrations...
.venv\Scripts\python.exe manage.py migrate

echo [2/4] Applying custom DDL constraints...
.venv\Scripts\python.exe manage.py apply_constraints

echo [3/4] Seeding database with algorithmic edge cases...
.venv\Scripts\python.exe manage.py seed_db

echo [4/4] Starting Django development server...
.venv\Scripts\python.exe manage.py runserver
pause