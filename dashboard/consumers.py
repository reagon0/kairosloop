# dashboard/consumers.py
"""
WebSocket consumers for live gauge data and commands.

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

Clients can send commands like:
    {
        "type": "command",
        "command": "set_filter",
        "level": 2
    }
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async


class GaugeConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live gauge readings and commands."""
    
    async def connect(self):
        # Get channel from URL, default to "all"
        self.gauge_channel = self.scope['url_route']['kwargs'].get('channel', 'all')
        self.room_group_name = f'gauge_{self.gauge_channel}'
        
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
            
            elif message_type == 'command':
                # Handle commands from dashboard
                await self.handle_command(data)
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_command(self, data):
        """Handle commands from the dashboard."""
        command = data.get('command')
        
        try:
            if command == 'set_filter':
                level = data.get('level', 5)
                await self.cmd_set_filter(level)
                await self.send_command_response(command, True, f'Filter set to level {level}')
            
            elif command == 'master_channel':
                channel = data.get('channel', 0)
                await self.cmd_master_channel(channel)
                await self.send_command_response(command, True, f'Channel {channel} mastered')
            
            elif command == 'master_all':
                await self.cmd_master_all()
                await self.send_command_response(command, True, 'All channels mastered')
            
            elif command == 'clear_masters':
                await self.cmd_clear_masters()
                await self.send_command_response(command, True, 'All master offsets cleared')
            
            else:
                await self.send_command_response(command, False, f'Unknown command: {command}')
        
        except Exception as e:
            await self.send_command_response(command, False, str(e))
    
    async def send_command_response(self, command, success, message):
        """Send command response back to client."""
        await self.send(text_data=json.dumps({
            'type': 'command_response',
            'command': command,
            'success': success,
            'message': message
        }))
    
    # =========================================================================
    # COMMAND IMPLEMENTATIONS
    # =========================================================================
    
    @sync_to_async
    def cmd_set_filter(self, level):
        """Set filter level on gauge service."""
        from devices.services import get_service
        service = get_service()
        if service.is_running:
            service.set_filter(level)
    
    @sync_to_async
    def cmd_master_channel(self, channel):
        """Master a single channel."""
        from devices.services import get_service
        service = get_service()
        if service.is_running:
            service.master_channel(channel)
    
    @sync_to_async
    def cmd_master_all(self):
        """Master all channels."""
        from devices.services import get_service
        service = get_service()
        if service.is_running:
            service.master_all()
    
    @sync_to_async
    def cmd_clear_masters(self):
        """Clear all master offsets."""
        from devices.services import get_service
        service = get_service()
        if service.is_running:
            service.clear_all_masters()
    
    # =========================================================================
    # EVENT HANDLERS (called by channel layer)
    # =========================================================================
    
    async def gauge_reading(self, event):
        """Send gauge reading to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def gauge_offset(self, event):
        """Send offset notification to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def gauge_status(self, event):
        """Send status update to WebSocket client."""
        await self.send(text_data=json.dumps(event))


# =============================================================================
# BROADCAST HELPERS (called from services.py)
# =============================================================================

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