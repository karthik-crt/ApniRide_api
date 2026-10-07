@echo off
echo Starting ApniRide Backend Services...

:: Start Celery Worker in a new window (using --pool=solo for Windows)
start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A ApniRide worker --pool=solo --loglevel=info"

:: Start Celery Beat in a new window
start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A ApniRide beat --loglevel=info"

:: Start Django Server in this window
echo Starting Django Development Server...
call venv\Scripts\activate
python manage.py runserver 192.168.1.40:8000
