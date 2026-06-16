@echo off
cd backend
call .venv\Scripts\activate
python manage.py test core.tests