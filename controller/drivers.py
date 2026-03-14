# controller/drivers.py
"""
Controller drivers - interface between KairosLoop and CNC/PLC.

Each driver implements the same interface, allowing KairosLoop
to work with different controllers (Fanuc, Mitsubishi, Siemens, Test).
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class MachineState(str, Enum):
    """Machine operating state."""
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'
    ALARM = 'ALARM'
    TOOL_CHANGE = 'TOOL_CHANGE'
    DISCONNECTED = 'DISCONNECTED'


class Signal(str, Enum):
    """Signals between KairosLoop and Controller."""
    # Outbound (KairosLoop → Controller)
    OFFSET_UPDATE = 'OFFSET_UPDATE'
    ALARM = 'ALARM'
    WARN = 'WARN'
    TOOL_CHANGE_REQUEST = 'TOOL_CHANGE_REQUEST'
    
    # Inbound (Controller → KairosLoop)
    CYCLE_COMPLETE = 'CYCLE_COMPLETE'
    ALARM_ACK = 'ALARM_ACK'
    TOOL_CHANGED = 'TOOL_CHANGED'
    PROGRAM_START = 'PROGRAM_START'
    PROGRAM_STOP = 'PROGRAM_STOP'
    STATE_CHANGE = 'STATE_CHANGE'


class ControllerStatus:
    """Current status of the controller connection."""
    def __init__(
        self,
        connected: bool = False,
        state: MachineState = MachineState.DISCONNECTED,
        alarm_active: bool = False,
        alarm_message: str = '',
        part_count: int = 0,
        cycle_active: bool = False,
        tool_offsets: Dict[int, Dict[str, float]] = None,
        tool_wear: Dict[int, float] = None,
    ):
        self.connected = connected
        self.state = state
        self.alarm_active = alarm_active
        self.alarm_message = alarm_message
        self.part_count = part_count
        self.cycle_active = cycle_active
        self.tool_offsets = tool_offsets or {}
        self.tool_wear = tool_wear or {}
    
    def to_dict(self) -> dict:
        return {
            'connected': self.connected,
            'state': self.state.value,
            'alarm_active': self.alarm_active,
            'alarm_message': self.alarm_message,
            'part_count': self.part_count,
            'cycle_active': self.cycle_active,
            'tool_offsets': {str(k): v for k, v in self.tool_offsets.items()},
            'tool_wear': {str(k): v for k, v in self.tool_wear.items()},
        }


# =============================================================================
# BASE CONTROLLER (Abstract Interface)
# =============================================================================

class BaseController(ABC):
    """
    Abstract base class for all controller drivers.
    
    Defines the interface that KairosLoop uses to communicate
    with CNC controllers. Implementations handle the protocol-specific
    details (FOCAS2, MT-Link, etc.)
    """
    
    def __init__(self):
        self._connected = False
        self._signal_handlers: Dict[Signal, List[Callable]] = {}
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    # === CONNECTION ===
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to controller."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection to controller."""
        pass
    
    # === OFFSETS ===
    
    @abstractmethod
    def write_offset(self, tool: int, axis: str, value: float) -> bool:
        """
        Write an offset adjustment to a tool register.
        
        Args:
            tool: Tool number (1-based)
            axis: Axis ('X', 'Y', 'Z')
            value: Offset value to ADD (not absolute)
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def read_offset(self, tool: int, axis: str) -> Optional[float]:
        """Read current offset value for a tool/axis."""
        pass
    
    # === SIGNALS ===
    
    @abstractmethod
    def send_alarm(self, message: str) -> bool:
        """Send alarm signal to controller (stops machine)."""
        pass
    
    @abstractmethod
    def send_warning(self, message: str) -> bool:
        """Send warning signal (doesn't stop machine)."""
        pass
    
    @abstractmethod
    def request_tool_change(self, tool: int) -> bool:
        """Request operator to change a tool."""
        pass
    
    # === STATUS ===
    
    @abstractmethod
    def get_status(self) -> ControllerStatus:
        """Get current controller/machine status."""
        pass
    
    # === SIGNAL HANDLING ===
    
    def on_signal(self, signal: Signal, handler: Callable):
        """Register a handler for an inbound signal."""
        if signal not in self._signal_handlers:
            self._signal_handlers[signal] = []
        self._signal_handlers[signal].append(handler)
    
    def _emit_signal(self, signal: Signal, data: dict = None):
        """Emit a signal to registered handlers."""
        data = data or {}
        for handler in self._signal_handlers.get(signal, []):
            try:
                handler(signal, data)
            except Exception as e:
                logger.exception(f"Error in signal handler for {signal}")


# =============================================================================
# TEST PLC DRIVER
# =============================================================================

class TestPLCDriver(BaseController):
    """
    Driver that communicates with TestPLC (simulated hardware).
    
    Used for testing and development without real CNC hardware.
    """
    
    def __init__(self, plc: 'TestPLC' = None, verbose: bool = True):
        super().__init__()
        self._plc = plc
        self._verbose = verbose
    
    def set_plc(self, plc: 'TestPLC'):
        """Set the TestPLC instance to communicate with."""
        self._plc = plc
        # Register for PLC signals
        plc.on_signal(self._handle_plc_signal)
    
    def _log(self, msg: str):
        if self._verbose:
            print(f"[TestPLCDriver] {msg}")
    
    def _handle_plc_signal(self, signal: Signal, data: dict):
        """Handle signals from the TestPLC."""
        self._emit_signal(signal, data)
    
    # === CONNECTION ===
    
    def connect(self) -> bool:
        if self._plc is None:
            self._log("No PLC configured")
            return False
        self._connected = True
        self._log("Connected to TestPLC")
        return True
    
    def disconnect(self):
        self._connected = False
        self._log("Disconnected from TestPLC")
    
    # === OFFSETS ===
    
    def write_offset(self, tool: int, axis: str, value: float) -> bool:
        if not self._connected or not self._plc:
            return False
        self._plc.write_offset(tool, axis, value)
        self._log(f"OFFSET T{tool} {axis}: {value:+.6f}")
        return True
    
    def read_offset(self, tool: int, axis: str) -> Optional[float]:
        if not self._connected or not self._plc:
            return None
        return self._plc.read_offset(tool, axis)
    
    # === SIGNALS ===
    
    def send_alarm(self, message: str) -> bool:
        if not self._connected or not self._plc:
            return False
        self._plc.receive_alarm(message)
        self._log(f"ALARM: {message}")
        return True
    
    def send_warning(self, message: str) -> bool:
        if not self._connected or not self._plc:
            return False
        self._plc.receive_warning(message)
        self._log(f"WARNING: {message}")
        return True
    
    def request_tool_change(self, tool: int) -> bool:
        if not self._connected or not self._plc:
            return False
        self._plc.receive_tool_change_request(tool)
        self._log(f"TOOL CHANGE REQUEST: T{tool}")
        return True
    
    # === STATUS ===
    
    def get_status(self) -> ControllerStatus:
        if not self._connected or not self._plc:
            return ControllerStatus(connected=False)
        
        state = self._plc.get_state()
        return ControllerStatus(
            connected=True,
            state=MachineState(state['state']),
            alarm_active=state['alarm_active'],
            alarm_message=state['alarm_message'],
            part_count=state['part_count_today'],
            cycle_active=state['cycle_active'],
            tool_offsets=state['tool_offsets'],
            tool_wear=state['tool_wear'],
        )


# =============================================================================
# FANUC FOCAS2 DRIVER (Stub)
# =============================================================================

class FanucDriver(BaseController):
    """
    Driver for Fanuc CNC via FOCAS2 protocol.
    
    TODO: Implement actual FOCAS2 communication.
    Requires Fanuc FOCAS2 library (Windows DLL or Linux .so)
    """
    
    def __init__(self, host: str, port: int = 8193):
        super().__init__()
        self.host = host
        self.port = port
        self._handle = None
    
    def connect(self) -> bool:
        # TODO: cnc_allclibhndl3(host, port, timeout, &handle)
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def disconnect(self):
        # TODO: cnc_freelibhndl(handle)
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def write_offset(self, tool: int, axis: str, value: float) -> bool:
        # TODO: cnc_wrtofs(handle, offset_num, axis, length, &data)
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def read_offset(self, tool: int, axis: str) -> Optional[float]:
        # TODO: cnc_rdtofs(handle, offset_num, axis, length, &data)
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def send_alarm(self, message: str) -> bool:
        # TODO: Write to PMC address or macro variable
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def send_warning(self, message: str) -> bool:
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def request_tool_change(self, tool: int) -> bool:
        raise NotImplementedError("FOCAS2 not yet implemented")
    
    def get_status(self) -> ControllerStatus:
        raise NotImplementedError("FOCAS2 not yet implemented")