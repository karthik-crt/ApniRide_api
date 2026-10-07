#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApniRide.settings')
    
    # Check if we are running the development server
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        # Prevent starting Celery multiple times if auto-reloader restarts the server
        if os.environ.get('RUN_MAIN') != 'true':
            import subprocess
            print("🚀 Starting Celery Worker and Beat in separate windows...")
            # Spawning Celery Worker in a new terminal window (using --pool=solo for Windows compatibility)
            subprocess.Popen('start "Celery Worker" cmd /k "venv\\Scripts\\activate && celery -A ApniRide worker --pool=solo --loglevel=info"', shell=True)
            # Spawning Celery Beat in a new terminal window
            subprocess.Popen('start "Celery Beat" cmd /k "venv\\Scripts\\activate && celery -A ApniRide beat --loglevel=info"', shell=True)
            
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
