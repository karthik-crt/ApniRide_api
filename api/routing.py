from django.urls import path,re_path
from . import consumers

websocket_urlpatterns = [
    path("ws/live-tracking/<ride_id>/", consumers.LiveTrackingConsumer.as_asgi()),
    re_path(r'^ws/driver/location/$', consumers.DriverLocationConsumer.as_asgi()),
]

