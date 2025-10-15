from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Use your actual project folder here
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApniRide.settings')

app = Celery('ApniRide')

# Load config from Django settings, using CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all apps
app.autodiscover_tasks()
