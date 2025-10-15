# ApniRide/firebase_app.py
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin_app = firebase_admin.initialize_app(cred)

# def send_multicast(tokens, notification=None, data=None):
#     """
#     Send FCM multicast notification to multiple devices
#     """
#     message = messaging.MulticastMessage(
#         tokens=tokens,
#         notification=messaging.Notification(**notification) if notification else None,
#         data=data or {}
#     )
#     return messaging.send_each_for_multicast(message)  # returns BatchResponse

def send_multicast(tokens, notification=None, data=None):
    """
    Send FCM multicast notification to multiple devices
    """
    android_config = messaging.AndroidConfig(
        priority='high',  # High priority for the overall message delivery
        notification=messaging.AndroidNotification(
            title=notification.get('title'),  # Reuse your title
            body=notification.get('body'),    # Reuse your body
            sound='buzzer',                   # Custom sound file name (without extension, must match your raw resource)
            channel_id='ride_channel',        # Your custom channel ID from Flutter code (ensures high importance/priority)
            priority='max'                    # Max priority for heads-up pop-up
        )
    ) if notification else None
 
    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(**notification) if notification else None,  # Keep for iOS/cross-platform
        android=android_config,  # Android-specific overrides
        data=data or {}
    )
    return messaging.send_each_for_multicast(message)  # returns BatchResponse

def send_fcm_notification(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token
    )
    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
    except Exception as e:
        print(f"Error sending FCM notification: {e}")