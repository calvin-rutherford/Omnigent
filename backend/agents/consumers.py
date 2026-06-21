import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BrokerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'broker_events'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': 'Connected to Omnigent Broker.'
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        # Echo back the user's message immediately so the UI feels responsive
        await self.send(text_data=json.dumps({
            'type': 'event',
            'message': f"You > {message}"
        }))

        # Dispatch to Celery to have the BrokerAgent (LLM) process it asynchronously
        from .tasks import process_broker_message
        process_broker_message.delay(message)

    # Receive message from room group
    async def broker_event(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'event',
            'message': message
        }))
