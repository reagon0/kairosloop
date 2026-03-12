# dashboard/consumers.py
"""
WebSocket consumers for live gauge data.

Clients connect to:
    ws://localhost:8000/ws/gauge/        (all channels)
    ws://localhost:8000/ws/gauge/0/      (specific channel)

Server pushes messages like:
    {
        "type": "gauge_reading",
        "channel": 0,
        "value": 25.4023,
        "timestamp": "2026-03-12T06:18:45.288Z",
        "in_tolerance": true
    }
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class GaugeConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live gauge readings."""
    
    async def connect(self):
        # Get channel from URL, default to "all"
        self.gauge_channel = self.scope['url_route']['kwargs'].get('channel', 'all')
        self.room_group_name = f'gauge_{self.gauge_channel}'
        
        print(f"DEBUG: Joining groups: {self.room_group_name}, gauge_all")  # ADD THIS
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Also join "all" group to receive all readings
        await self.channel_layer.group_add(
            'gauge_all',
            self.channel_name
        )
        
        await self.accept()
        
        print(f"DEBUG: WebSocket connected, channel_name={self.channel_name}")  # ADD THIS
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'channel': self.gauge_channel,
            'message': f'Connected to gauge channel: {self.gauge_channel}'
        }))



    
    async def disconnect(self, close_code):
        # Leave room groups
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            'gauge_all',
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            
            elif message_type == 'subscribe':
                # Subscribe to a specific channel
                channel = data.get('channel', 'all')
                await self.channel_layer.group_add(
                    f'gauge_{channel}',
                    self.channel_name
                )
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'channel': channel
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def gauge_reading(self, event):
        """Send gauge reading to WebSocket client."""
        print(f"DEBUG: gauge_reading called with {event}")  # ADD THIS
        await self.send(text_data=json.dumps(event))
    
    async def gauge_offset(self, event):
        """Send offset notification to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def gauge_status(self, event):
        """Send status update to WebSocket client."""
        await self.send(text_data=json.dumps(event))


# -------------------------------------------------------------------------
# Helper functions to broadcast from services.py
# -------------------------------------------------------------------------

def broadcast_reading(channel: int, value: float, timestamp, in_tolerance: bool = True):
    """
    Broadcast a gauge reading to all connected WebSocket clients.
    Call this from services.py when a new reading comes in.
    """
    channel_layer = get_channel_layer()
    
    message = {
        'type': 'gauge_reading',
        'channel': channel,
        'value': value,
        'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
        'in_tolerance': in_tolerance
    }
    
    # Send to channel-specific group
    async_to_sync(channel_layer.group_send)(
        f'gauge_{channel}',
        message
    )
    
    # Send to "all" group
    async_to_sync(channel_layer.group_send)(
        'gauge_all',
        message
    )


def broadcast_offset(controller: str, tool_number: int, offset_value: float, success: bool):
    """Broadcast an offset event to all connected clients."""
    channel_layer = get_channel_layer()
    
    message = {
        'type': 'gauge_offset',
        'controller': controller,
        'tool_number': tool_number,
        'offset_value': offset_value,
        'success': success
    }
    
    async_to_sync(channel_layer.group_send)(
        'gauge_all',
        message
    )


def broadcast_status(status: str, message: str = ''):
    """Broadcast a status update to all connected clients."""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'gauge_all',
        {
            'type': 'gauge_status',
            'status': status,
            'message': message
        }
    )