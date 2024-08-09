# consumers.py

import json
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class DeliveryBoyLocationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f'order_{self.order_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def status_update(self, event):
        # Send location update to client
        await self.send_json({
            'message': event['message']
        })
