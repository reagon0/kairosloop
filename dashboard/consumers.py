# dashboard/consumers.py
"""
WebSocket consumers for live gauge data and commands.

Clients connect to:
    ws://localhost:8000/ws/gauge/        (all channels)
    ws://localhost:8000/ws/gauge/0/      (specific channel)
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
        
        # Send initial machine state
        state = await self.get_machine_state()
        await self.send(text_data=json.dumps({
            'type': 'machine_state',
            **state
        }))
        
        # Send initial tool assignments state
        tool_state = await self.get_tool_assignments_state()
        await self.send(text_data=json.dumps({
            'type': 'tool_assignments_state',
            'assignments': tool_state
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
            # Gauge commands
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
            
            elif command == 'capture':
                result = await self.cmd_capture()
                await self.send_command_response(command, True, f'Captured {len(result.feature_results)} features')
            
            # Machine commands
            elif command == 'machine_start':
                success = await self.cmd_machine_start()
                await self.send_command_response(command, success, 'Machine started' if success else 'Failed to start')
            
            elif command == 'machine_stop':
                await self.cmd_machine_stop()
                await self.send_command_response(command, True, 'Machine stopped')
            
            elif command == 'machine_ack_alarm':
                success = await self.cmd_machine_ack_alarm()
                await self.send_command_response(command, success, 'Alarm acknowledged' if success else 'No alarm to acknowledge')
            
            elif command == 'machine_reset_count':
                await self.cmd_machine_reset_count()
                await self.send_command_response(command, True, 'Part count reset')
            
            elif command == 'machine_change_tool':
                tool = data.get('tool', 1)
                await self.cmd_machine_change_tool(tool)
                await self.send_command_response(command, True, f'Tool T{tool} changed')
            
            elif command == 'get_machine_state':
                state = await self.get_machine_state()
                await self.send(text_data=json.dumps({
                    'type': 'machine_state',
                    **state
                }))
            
            # Simulation commands
            elif command == 'simulation_start':
                await self.cmd_simulation_start()
                await self.send_command_response(command, True, 'Simulation started')
            
            elif command == 'simulation_stop':
                await self.cmd_simulation_stop()
                await self.send_command_response(command, True, 'Simulation stopped')
            
            elif command == 'simulation_set_wear_rate':
                tool = data.get('tool', 1)
                rate = data.get('rate', 0.0005)
                await self.cmd_set_wear_rate(tool, rate)
                await self.send_command_response(command, True, f'T{tool} wear rate set to {rate}')
            
            elif command == 'simulation_induce_wear':
                tool = data.get('tool', 1)
                amount = data.get('amount', 0.01)
                await self.cmd_induce_wear(tool, amount)
                await self.send_command_response(command, True, f'T{tool} wear induced +{amount}')
            
            elif command == 'simulation_reset':
                await self.cmd_simulation_reset()
                await self.send_command_response(command, True, 'Simulation reset')
            
            elif command == 'simulation_set_cycle_time':
                cycle_time = data.get('cycle_time', 3.0)
                await self.cmd_set_cycle_time(cycle_time)
                await self.send_command_response(command, True, f'Cycle time set to {cycle_time}s')
            
            elif command == 'get_tool_assignments':
                state = await self.get_tool_assignments_state()
                await self.send(text_data=json.dumps({
                    'type': 'tool_assignments_state',
                    'assignments': state
                }))
            
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
    # GAUGE COMMAND IMPLEMENTATIONS
    # =========================================================================
    
    @sync_to_async
    def cmd_set_filter(self, level):
        """Set filter level on gauge service."""
        from measurement.services import get_service
        service = get_service()
        if service.is_running:
            service.set_filter(level)
    
    @sync_to_async
    def cmd_master_channel(self, channel):
        """Master a single channel."""
        from measurement.services import get_service
        service = get_service()
        if service.is_running:
            service.master_channel(channel)
    
    @sync_to_async
    def cmd_master_all(self):
        """Master all channels."""
        from measurement.services import get_service
        service = get_service()
        if service.is_running:
            service.master_all()
    
    @sync_to_async
    def cmd_clear_masters(self):
        """Clear all master offsets."""
        from measurement.services import get_service
        service = get_service()
        if service.is_running:
            service.clear_all_masters()

    @sync_to_async
    def cmd_capture(self):
        """Execute a measurement capture."""
        from measurement.capture import capture_measurement
        return capture_measurement(source='manual')
    
    # =========================================================================
    # MACHINE COMMAND IMPLEMENTATIONS
    # =========================================================================
    
    @sync_to_async
    def get_machine_state(self):
        """Get current machine/PLC state."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        return plc.get_state()
    
    @sync_to_async
    def cmd_machine_start(self):
        """Start the machine."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        return plc.operator_start()
    
    @sync_to_async
    def cmd_machine_stop(self):
        """Stop the machine."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        plc.operator_stop()
    
    @sync_to_async
    def cmd_machine_ack_alarm(self):
        """Acknowledge alarm."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        return plc.operator_ack_alarm()
    
    @sync_to_async
    def cmd_machine_reset_count(self):
        """Reset part count."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        plc.operator_reset_part_count()
    
    @sync_to_async
    def cmd_machine_change_tool(self, tool):
        """
        Change a tool (reset tool assignment).
        
        This creates a new ToolAssignment record for historical tracking.
        Also updates any CompensationRules to point to the new assignment.
        """
        from simulator.plc import get_test_plc
        from tooling.models import ToolAssignment
        from controller.models import ControllerConfig
        from compensation.models import CompensationRule
        
        plc = get_test_plc()
        plc.operator_change_tool(tool)
        
        # Find and replace the active tool assignment for this position
        # Get the test controller
        controller = ControllerConfig.objects.filter(protocol='TEST').first()
        if controller:
            assignment = ToolAssignment.get_active(controller, tool)
            if assignment:
                # Get rules pointing to old assignment BEFORE replacing
                old_assignment_id = assignment.id
                
                new_assignment = assignment.replace()
                
                # Update all CompensationRules that pointed to old assignment
                updated = CompensationRule.objects.filter(
                    tool_assignment_id=old_assignment_id
                ).update(tool_assignment=new_assignment)
                
                if updated:
                    print(f"[Tool Change] Updated {updated} compensation rule(s) to new assignment")
                
                # Broadcast the update
                broadcast_tool_assignment_update(new_assignment)
    
    # =========================================================================
    # TOOL ASSIGNMENT STATE
    # =========================================================================
    
    @sync_to_async
    def get_tool_assignments_state(self):
        """Get current tool assignments for dashboard."""
        from tooling.models import ToolAssignment, AssignmentStatus
        
        assignments = ToolAssignment.objects.filter(
            status__in=[AssignmentStatus.ACTIVE, AssignmentStatus.WARNING, AssignmentStatus.CHANGE_REQUIRED]
        ).select_related('tool_instance', 'tool_instance__tool_type', 'controller')
        
        return [
            {
                'id': a.id,
                'uuid': str(a.uuid),
                'tool_position': a.tool_position,
                'tool_name': a.tool_instance.tool_type.name,
                'controller_name': a.controller.name,
                'accumulated_offset': a.accumulated_offset,
                'usage_percentage': a.usage_percentage,
                'max_offset': a.tool_instance.tool_type.max_offset_distance,
                'status': a.status,
                'installed_at': a.installed_at.isoformat(),
                'cycle_count': a.cycle_count,
            }
            for a in assignments
        ]
    
    # =========================================================================
    # SIMULATION COMMAND IMPLEMENTATIONS
    # =========================================================================
    
    @sync_to_async
    def cmd_simulation_start(self):
        """Start the full simulation loop."""
        from simulator.plc import get_test_plc
        from simulator.tool_wear import get_tool_wear_simulation
        from dashboard.consumers import broadcast_machine_state
        
        # Check if configuration is valid before starting
        try:
            from simulator.seed import is_valid, get_missing
            if not is_valid():
                missing = get_missing()
                raise Exception(f"Configuration incomplete: {', '.join(missing)}")
        except ImportError:
            pass  # seed module not available, skip validation
        
        plc = get_test_plc()
        tool_wear = get_tool_wear_simulation()
        
        # Wire callbacks
        plc.set_state_callback(broadcast_machine_state)
        
        # Enable simulation and start
        plc.enable_simulation(tool_wear)
        plc.start()
    
    @sync_to_async
    def cmd_simulation_stop(self):
        """Stop the simulation."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        plc.disable_simulation()
        plc.operator_stop()
    
    @sync_to_async
    def cmd_set_wear_rate(self, tool, rate):
        """Set wear rate for a tool."""
        from simulator.tool_wear import get_tool_wear_simulation
        tool_wear = get_tool_wear_simulation()
        tool_wear.set_wear_rate(tool, rate)
    
    @sync_to_async
    def cmd_induce_wear(self, tool, amount):
        """Induce wear on a tool (for demos)."""
        from simulator.tool_wear import get_tool_wear_simulation
        tool_wear = get_tool_wear_simulation()
        tool_wear.induce_wear(tool, amount)
    
    @sync_to_async
    def cmd_simulation_reset(self):
        """Reset the simulation and clear database."""
        from simulator.plc import get_test_plc
        from simulator.tool_wear import get_tool_wear_simulation
        from measurement.models import Measurement
        from compensation.models import CompensationEvent
        from tooling.models import ToolAssignment, AssignmentStatus
        
        plc = get_test_plc()
        tool_wear = get_tool_wear_simulation()
        
        # Stop simulation
        plc.operator_stop()
        plc.disable_simulation()
        tool_wear.reset_all()
        plc.operator_reset_part_count()
        
        # Reset tool offsets in PLC
        for t in range(1, 11):
            plc._tool_offsets[t] = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
            plc._tool_wear[t] = 0.0
        
        # Clear database
        Measurement.objects.all().delete()
        CompensationEvent.objects.all().delete()
        
        # Reset tool assignments (keep them, just reset counters)
        ToolAssignment.objects.filter(
            status__in=[AssignmentStatus.ACTIVE, AssignmentStatus.WARNING, AssignmentStatus.CHANGE_REQUIRED]
        ).update(
            accumulated_offset=0.0,
            cycle_count=0,
            status=AssignmentStatus.ACTIVE
        )
        
        # Also reset tool instances
        from tooling.models import ToolInstance, InstanceStatus
        ToolInstance.objects.filter(status=InstanceStatus.IN_USE).update(
            total_parts_cut=0,
            total_accumulated_wear=0.0
        )
        
        # Broadcast state (alarm may still be active - operator must clear it)
        plc._broadcast_state()
        
        print("[Reset] Simulation and database cleared")
    
    @sync_to_async
    def cmd_set_cycle_time(self, cycle_time):
        """Set the cycle time."""
        from simulator.plc import get_test_plc
        plc = get_test_plc()
        plc.cycle_time = cycle_time
    
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

    async def capture_result(self, event):
        """Send capture result to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def machine_state(self, event):
        """Send machine state update to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def simulation_state(self, event):
        """Send simulation state update to WebSocket client."""
        await self.send(text_data=json.dumps(event))
    
    async def tool_assignment_update(self, event):
        """Send tool assignment update to WebSocket client."""
        await self.send(text_data=json.dumps(event))


# =============================================================================
# BROADCAST HELPERS (called from services.py and simulators)
# =============================================================================

def broadcast_reading(channel: int, value: float, timestamp, in_tolerance: bool = True):
    """Broadcast a gauge reading to all connected WebSocket clients."""
    channel_layer = get_channel_layer()
    
    message = {
        'type': 'gauge_reading',
        'channel': channel,
        'value': value,
        'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
        'in_tolerance': in_tolerance
    }
    
    async_to_sync(channel_layer.group_send)(
        f'gauge_{channel}',
        message
    )
    
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


def broadcast_machine_state(state: dict):
    """Broadcast machine state to all connected clients."""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'gauge_all',
        {
            'type': 'machine_state',
            **state
        }
    )


def broadcast_tool_assignment_update(assignment):
    """Broadcast tool assignment update to all connected clients."""
    channel_layer = get_channel_layer()
    
    tool_type = assignment.tool_instance.tool_type
    
    async_to_sync(channel_layer.group_send)(
        'gauge_all',
        {
            'type': 'tool_assignment_update',
            'tool_assignment': {
                'id': assignment.id,
                'uuid': str(assignment.uuid),
                'tool_position': assignment.tool_position,
                'tool_name': tool_type.name,
                'controller_name': assignment.controller.name,
                'accumulated_offset': assignment.accumulated_offset,
                'usage_percentage': assignment.usage_percentage,
                'max_offset': tool_type.max_offset_distance,
                'status': assignment.status,
                'installed_at': assignment.installed_at.isoformat(),
                'cycle_count': assignment.cycle_count,
            }
        }
    )