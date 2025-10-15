import json
from channels.generic.websocket import AsyncWebsocketConsumer

from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class LiveTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group_name = f"ride_{self.ride_id}"

        # Add this connection to the ride group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        


    async def disconnect(self, close_code):
        # Remove from group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        

    async def receive(self, text_data):
        print("text_data",text_data)
        data = json.loads(text_data)
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        # Broadcast to all clients in this ride group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "location_update",
                "latitude": latitude,
                "longitude": longitude
            }
        )

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            "latitude": event["latitude"],
            "longitude": event["longitude"]
        }))


#For driver location update
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class DriverLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"WebSocket connecting: {self.scope['query_string']}")
        query_string = self.scope['query_string'].decode()
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]

        if token:
            user = await self.get_user_from_token(token)
            if user and user.is_authenticated:
                self.scope['user'] = user
                self.driver_id = user.id
                self.group_name = f"driver_{self.driver_id}"
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                await self.accept()
                logger.info(f"WebSocket connected for driver {self.driver_id}")
                await self.send(text_data=json.dumps({
                    "status": "connected",
                    "driver_id": self.driver_id
                }))
            else:
                logger.warning("WebSocket connection rejected: Invalid or unauthenticated token")
                await self.close(code=4001)
        else:
            logger.warning("WebSocket connection rejected: No token provided")
            await self.close(code=4002)

    @database_sync_to_async
    def get_user_from_token(self, token):
        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            logger.info(f"User authenticated: {user.id} ({user.username})")
            return user
        except Exception as e:
            logger.error(f"Token authentication failed: {str(e)}")
            return AnonymousUser()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WebSocket disconnected for driver {self.driver_id}, code {close_code}")
        else:
            logger.info(f"WebSocket disconnected before group assignment, code {close_code}")

    async def receive(self, text_data):
        """Handle location updates from driver"""
        data = json.loads(text_data)
        logger.info(f"Location update from driver {self.scope['user'].id}: {data}")
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "location_update",
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "driver": self.scope['user'].id
            }
        )

    async def location_update(self, event):
        logger.info(f"Sending location update to driver {self.driver_id}: {event}")
        await self.send(text_data=json.dumps({
            "type": "location_update",
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "driver": event["driver"]
        }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RideLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.room_group_name = f"ride_{self.ride_id}"

        # Join ride group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave ride group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        latitude = data.get("lat")
        longitude = data.get("lng")

        # Broadcast location to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "location_update",
                "lat": latitude,
                "lng": longitude
            }
        )

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            "lat": event["lat"],
            "lng": event["lng"]
        }))

