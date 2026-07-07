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
        
        # Check if it's an approval response
        if text_data_json.get('type') == 'approval_response':
            import redis
            from django.conf import settings
            r = redis.Redis.from_url(settings.CELERY_RESULT_BACKEND)
            approval_id = text_data_json.get('id')
            approved = text_data_json.get('approved')
            status = "approved" if approved else "denied"
            r.set(f"approval:{approval_id}", status)
            return

        message = text_data_json.get('message', '')
        stateful = text_data_json.get('stateful', True)

        # Echo back the user's message immediately so the UI feels responsive
        await self.send(text_data=json.dumps({
            'type': 'event',
            'message': f"You > {message}"
        }))

        # Dispatch to Celery to have the BrokerAgent (LLM) process it asynchronously
        from .tasks import process_broker_message
        process_broker_message.delay(message, stateful=stateful)

    # Receive message from room group
    async def broker_event(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'event',
            'message': message
        }))
        
    async def approval_request(self, event):
        # Send approval request to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'approval_request',
            'approval_id': event['approval_id'],
            'command': event['command']
        }))
