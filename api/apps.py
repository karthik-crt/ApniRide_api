import sys
import threading
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"


    def ready(self):
        import ApniRide.firebase_app
        # APScheduler has been disabled in favor of Celery Beat
