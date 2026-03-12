# devices/controllers.py
"""
Controller interface and implementations.
The receiving device (CNC controller) is abstracted so we can swap between:
- TestController (for development)
- FanucController (production)
- SiemensController (future)
- etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class ControllerState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class OffsetRecord:
    """Record of an offset sent to controller."""
    tool_number: int
    offset_value: float
    timestamp: datetime
    acknowledged: bool = False


class BaseController(ABC):
    """
    Abstract base class for CNC controllers.
    Implement this for each controller type.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Controller name for logging."""
        pass
    
    @property
    @abstractmethod
    def state(self) -> ControllerState:
        """Current connection state."""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to controller.
        Returns True if successful.
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection."""
        pass
    
    @abstractmethod
    def write_offset(self, tool_number: int, offset_value: float) -> bool:
        """
        Write tool wear offset.
        Returns True if acknowledged.
        """
        pass
    
    @abstractmethod
    def read_offset(self, tool_number: int) -> Optional[float]:
        """Read current tool offset value."""
        pass
    
    @abstractmethod
    def write_macro(self, variable: int, value: float) -> bool:
        """Write to macro variable."""
        pass
    
    @abstractmethod
    def read_macro(self, variable: int) -> Optional[float]:
        """Read macro variable."""
        pass


class TestController(BaseController):
    """
    Test controller for development.
    Stores values in memory, logs all operations.
    """
    
    def __init__(self, verbose: bool = True):
        self._state = ControllerState.DISCONNECTED
        self._verbose = verbose
        self._offsets: Dict[int, float] = {}
        self._macros: Dict[int, float] = {}
        self._history: List[OffsetRecord] = []
    
    @property
    def name(self) -> str:
        return "TestController"
    
    @property
    def state(self) -> ControllerState:
        return self._state
    
    @property
    def history(self) -> List[OffsetRecord]:
        """Get history of all offsets sent."""
        return self._history.copy()
    
    def connect(self) -> bool:
        self._state = ControllerState.CONNECTED
        self._log("Connected")
        return True
    
    def disconnect(self):
        self._state = ControllerState.DISCONNECTED
        self._log("Disconnected")
    
    def write_offset(self, tool_number: int, offset_value: float) -> bool:
        if self._state != ControllerState.CONNECTED:
            self._log(f"ERROR: Not connected")
            return False
        
        self._offsets[tool_number] = offset_value
        record = OffsetRecord(
            tool_number=tool_number,
            offset_value=offset_value,
            timestamp=datetime.now(),
            acknowledged=True
        )
        self._history.append(record)
        self._log(f"OFFSET T{tool_number}: {offset_value:+.6f} mm")
        return True
    
    def read_offset(self, tool_number: int) -> Optional[float]:
        if self._state != ControllerState.CONNECTED:
            return None
        return self._offsets.get(tool_number, 0.0)
    
    def write_macro(self, variable: int, value: float) -> bool:
        if self._state != ControllerState.CONNECTED:
            self._log(f"ERROR: Not connected")
            return False
        
        self._macros[variable] = value
        self._log(f"MACRO #{variable} = {value}")
        return True
    
    def read_macro(self, variable: int) -> Optional[float]:
        if self._state != ControllerState.CONNECTED:
            return None
        return self._macros.get(variable)
    
    def reset(self):
        """Clear all stored values."""
        self._offsets.clear()
        self._macros.clear()
        self._history.clear()
        self._log("Reset")
    
    def _log(self, message: str):
        if self._verbose:
            print(f"[{self.name}] {message}")


class FanucController(BaseController):
    """
    Fanuc controller via RS-232.
    TODO: Implement when machine details are confirmed.
    """
    
    def __init__(self, port: str = "COM1", baudrate: int = 9600):
        self._port = port
        self._baudrate = baudrate
        self._state = ControllerState.DISCONNECTED
        self._serial = None  # Will be serial.Serial
    
    @property
    def name(self) -> str:
        return f"Fanuc ({self._port})"
    
    @property
    def state(self) -> ControllerState:
        return self._state
    
    def connect(self) -> bool:
        # TODO: Implement serial connection
        # import serial
        # self._serial = serial.Serial(self._port, self._baudrate, timeout=1)
        raise NotImplementedError("Fanuc connection not yet implemented")
    
    def disconnect(self):
        raise NotImplementedError()
    
    def write_offset(self, tool_number: int, offset_value: float) -> bool:
        raise NotImplementedError()
    
    def read_offset(self, tool_number: int) -> Optional[float]:
        raise NotImplementedError()
    
    def write_macro(self, variable: int, value: float) -> bool:
        raise NotImplementedError()
    
    def read_macro(self, variable: int) -> Optional[float]:
        raise NotImplementedError()