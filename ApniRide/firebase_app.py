# ApniRide/firebase_app.py
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin_app = firebase_admin.initialize_app(cred)



def send_multicast(tokens, notification=None, data=None):
    """
    Send FCM multicast notification to multiple devices
    """
    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(**notification) if notification else None,
        data=data or {}
    )
    return messaging.send_each_for_multicast(message)  # returns BatchResponse
