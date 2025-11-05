# ApniRide/firebase_app.py
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin_app = firebase_admin.initialize_app(cred)

def send_Offer(tokens, notification=None, data=None):
    """
    Send FCM multicast notification to multiple devices
    """
    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(**notification) if notification else None,
        data=data or {}
    )
    return messaging.send_each_for_multicast(message)  

def send_multicast(tokens, notification=None, data=None):
    """
    Send FCM multicast notification to multiple devices
    """
    android_config = messaging.AndroidConfig(
        priority='high',  
        notification=messaging.AndroidNotification(
            title=notification.get('title'),  
            body=notification.get('body'),    
            sound='buzzer',                   
            channel_id='ride_channel',       
            priority='max'                    
        )
    ) if notification else None
 
    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(**notification) if notification else None,  
        android=android_config,  
        data=data or {}
    )
    return messaging.send_each_for_multicast(message)  

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