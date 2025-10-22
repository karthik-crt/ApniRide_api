import sys
import threading
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"


    def ready(self):
        import ApniRide.firebase_app
        if "runserver" in sys.argv or "daphne" in sys.argv:
            from . import scheduler
            # Delay scheduler start by 1 second so Django finishes init
            threading.Timer(1, scheduler.start).start()
