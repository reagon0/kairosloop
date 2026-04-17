# controller/gateway.py
"""
Offset Gateway - Safety layer between compensation and hardware.

All offset requests flow through here. The gateway:
1. Validates the request
2. Checks guardrails (tool limits, machine limits)
3. Accepts or rejects
4. Sends to driver if accepted
5. Updates ToolAssignment tracking
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


class OffsetDecision(str, Enum):
    """Gateway decision on an offset request."""
    ACCEPTED = 'ACCEPTED'
    ACCEPTED_WARNING = 'ACCEPTED_WARNING'  # Accepted but approaching limit
    REJECTED_LIMIT = 'REJECTED_LIMIT'  # Would exceed tool limit
    REJECTED_BLOCKED = 'REJECTED_BLOCKED'  # Tool requires change
    REJECTED_INVALID = 'REJECTED_INVALID'  # Invalid request
    REJECTED_OFFLINE = 'REJECTED_OFFLINE'  # Controller not connected
    ERROR = 'ERROR'  # Communication error


@dataclass
class OffsetRequest:
    """Request to apply an offset."""
    tool_assignment_id: int
    axis: str
    offset_value: float
    source: str = 'compensation'  # compensation, manual, etc.
    
    # Set by gateway during processing
    tool_assignment: Optional['ToolAssignment'] = None


@dataclass
class OffsetResult:
    """Result of an offset request."""
    decision: OffsetDecision
    offset_applied: float  # Actual offset sent (may be clamped)
    reason: str
    
    # State after application
    accumulated_before: float = 0.0
    accumulated_after: float = 0.0
    usage_percentage: float = 0.0
    
    @property
    def success(self) -> bool:
        return self.decision in (OffsetDecision.ACCEPTED, OffsetDecision.ACCEPTED_WARNING)


class OffsetGateway:
    """
    Gateway that controls all offset writes to controllers.
    
    Usage:
        gateway = OffsetGateway()
        
        request = OffsetRequest(
            tool_assignment_id=1,
            axis='X',
            offset_value=0.005,
        )
        
        result = gateway.submit(request)
        
        if result.success:
            print(f"Applied: {result.offset_applied}")
        else:
            print(f"Rejected: {result.reason}")
    """
    
    def __init__(self):
        self._drivers = {}  # controller_id -> driver instance
    
    def register_driver(self, controller_id: int, driver):
        """Register a driver for a controller."""
        self._drivers[controller_id] = driver
    
    def submit(self, request: OffsetRequest) -> OffsetResult:
        """
        Submit an offset request for validation and execution.
        
        Returns OffsetResult with decision and details.
        """
        from tooling.models import ToolAssignment, AssignmentStatus
        
        # 1. Load tool assignment
        try:
            assignment = ToolAssignment.objects.select_related(
                'tool_instance', 'tool_instance__tool_type', 'controller'
            ).get(id=request.tool_assignment_id)
            request.tool_assignment = assignment
        except ToolAssignment.DoesNotExist:
            return OffsetResult(
                decision=OffsetDecision.REJECTED_INVALID,
                offset_applied=0.0,
                reason=f"ToolAssignment {request.tool_assignment_id} not found",
            )
        
        # 2. Check if assignment is blocked (requires tool change)
        if assignment.status == AssignmentStatus.REPLACED:
            return OffsetResult(
                decision=OffsetDecision.REJECTED_INVALID,
                offset_applied=0.0,
                reason="Tool assignment has been replaced",
            )
        
        if assignment.status == AssignmentStatus.CHANGE_REQUIRED:
            return OffsetResult(
                decision=OffsetDecision.REJECTED_BLOCKED,
                offset_applied=0.0,
                reason="Tool change required before further compensation",
                accumulated_before=assignment.accumulated_offset,
                accumulated_after=assignment.accumulated_offset,
                usage_percentage=assignment.usage_percentage,
            )
        
        # 3. Check guardrails
        tool_type = assignment.tool_instance.tool_type
        current_accumulated = abs(assignment.accumulated_offset)
        proposed_accumulated = current_accumulated + abs(request.offset_value)
        max_allowed = tool_type.max_offset_distance
        
        # Would this exceed the limit?
        if proposed_accumulated > max_allowed:
            # Mark tool as needing change if at limit
            if assignment.status != AssignmentStatus.CHANGE_REQUIRED:
                assignment.status = AssignmentStatus.CHANGE_REQUIRED
                assignment.save(update_fields=['status'])
                
                # Check controller's on_tool_limit setting
                from controller.models import ToolLimitAction
                if assignment.controller.on_tool_limit == ToolLimitAction.ALARM:
                    # Trigger PLC alarm to stop the machine
                    try:
                        from simulator.plc import get_test_plc
                        plc = get_test_plc()
                        plc.trigger_alarm(f"T{assignment.tool_position} tool change required - compensation blocked")
                    except Exception as e:
                        logger.warning(f"Could not trigger PLC alarm: {e}")
            
            # Broadcast so UI shows blocked state
            self._broadcast_update(assignment, blocked=True)
            
            return OffsetResult(
                decision=OffsetDecision.REJECTED_LIMIT,
                offset_applied=0.0,
                reason=f"Would exceed tool limit ({proposed_accumulated:.4f} > {max_allowed:.4f})",
                accumulated_before=current_accumulated,
                accumulated_after=current_accumulated,
                usage_percentage=assignment.usage_percentage,
            )
        
        # 4. Get driver and check connection
        driver = self._get_driver(assignment.controller)
        if driver is None:
            return OffsetResult(
                decision=OffsetDecision.REJECTED_OFFLINE,
                offset_applied=0.0,
                reason=f"No driver registered for controller {assignment.controller.name}",
            )
        
        if not driver.connected:
            return OffsetResult(
                decision=OffsetDecision.REJECTED_OFFLINE,
                offset_applied=0.0,
                reason=f"Controller {assignment.controller.name} not connected",
            )
        
        # 5. Send offset to hardware
        try:
            success = driver.write_offset(
                tool=assignment.tool_position,
                axis=request.axis,
                value=request.offset_value
            )
        except Exception as e:
            logger.exception(f"Error writing offset to {assignment.controller.name}")
            return OffsetResult(
                decision=OffsetDecision.ERROR,
                offset_applied=0.0,
                reason=f"Communication error: {str(e)}",
                accumulated_before=current_accumulated,
                accumulated_after=current_accumulated,
                usage_percentage=assignment.usage_percentage,
            )
        
        if not success:
            return OffsetResult(
                decision=OffsetDecision.ERROR,
                offset_applied=0.0,
                reason="Driver returned failure",
                accumulated_before=current_accumulated,
                accumulated_after=current_accumulated,
                usage_percentage=assignment.usage_percentage,
            )
        
        # 6. Update tool assignment tracking
        assignment.apply_offset(request.offset_value)
        
        # 7. Determine if we're in warning zone
        new_percentage = assignment.usage_percentage
        
        # Get warning threshold (could come from rule or controller default)
        warning_threshold = 80.0  # Default 80%, could be configurable
        
        if new_percentage >= warning_threshold:
            decision = OffsetDecision.ACCEPTED_WARNING
            reason = f"Applied, but at {new_percentage:.1f}% of tool limit"
        else:
            decision = OffsetDecision.ACCEPTED
            reason = f"Applied successfully"
        
        logger.info(
            f"[Gateway] T{assignment.tool_position} {request.axis}: "
            f"{request.offset_value:+.6f} → {decision.value} "
            f"({new_percentage:.1f}% used)"
        )
        
        # 8. Broadcast state change
        self._broadcast_update(assignment)
        
        return OffsetResult(
            decision=decision,
            offset_applied=request.offset_value,
            reason=reason,
            accumulated_before=current_accumulated,
            accumulated_after=abs(assignment.accumulated_offset),
            usage_percentage=new_percentage,
        )
    
    def _get_driver(self, controller):
        """Get the driver for a controller."""
        # First check if explicitly registered
        if controller.id in self._drivers:
            return self._drivers[controller.id]
        
        # Fall back to test driver for simulator
        if controller.protocol == 'TEST':
            from controller.drivers import TestPLCDriver
            from simulator.plc import get_test_plc
            
            plc = get_test_plc()
            driver = TestPLCDriver(plc=plc)
            driver.set_plc(plc)
            driver.connect()
            
            self._drivers[controller.id] = driver
            return driver
        
        return None
    
    def _broadcast_update(self, assignment, blocked=False):
        """Broadcast tool assignment update to WebSocket clients."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
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
                        'accumulated_offset': assignment.accumulated_offset,
                        'usage_percentage': assignment.usage_percentage,
                        'status': assignment.status,
                        'max_offset': tool_type.max_offset_distance,
                        'blocked': blocked,
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Error broadcasting tool assignment update: {e}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_gateway_instance: Optional[OffsetGateway] = None


def get_gateway() -> OffsetGateway:
    """Get the singleton gateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = OffsetGateway()
    return _gateway_instance