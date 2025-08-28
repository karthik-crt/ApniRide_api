from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/live-tracking/<ride_id>/", consumers.LiveTrackingConsumer.as_asgi()),
]
