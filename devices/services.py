# devices/services.py
"""
Background service for gauge data acquisition and offset management.
Uses continuous mode for low-latency measurement.
"""

import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from django.utils import timezone

from .n1700 import N1700, N1700Exception, FilterLevel
from .controllers import BaseController, TestController, ControllerState
from .models import GaugeConfig, ChannelConfig, ControllerConfig, ToolMapping
from dmis.models import Feature, Measurement, Offset


class ServiceState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class ChannelStats:
    """Per-channel statistics."""
    count: int = 0
    last_value: Optional[float] = None
    last_time: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def update(self, value: float, timestamp: datetime):
        self.count += 1
        self.last_value = value
        self.last_time = timestamp
        if self.min_value is None or value < self.min_value:
            self.min_value = value
        if self.max_value is None or value > self.max_value:
            self.max_value = value
    
    def reset(self):
        self.count = 0
        self.last_value = None
        self.last_time = None
        self.min_value = None
        self.max_value = None


@dataclass
class ServiceConfig:
    """Configuration for the gauge service."""
    filter_level: int = 5  # Default: 32-sample averaging
    auto_offset: bool = False
    auto_save: bool = False  # Save measurements to database
    feature_map: Dict[int, int] = field(default_factory=dict)  # channel -> feature_id


class GaugeService:
    """
    Gauge data acquisition service using continuous mode.
    
    Streams measurements from N1700 hardware and broadcasts to WebSocket clients.
    Optionally saves to database and sends offsets to CNC controllers.
    """
    
    def __init__(self, dll_path: Optional[str] = None):
        self.dll_path = dll_path
        self.gauge: Optional[N1700] = None
        self.config = ServiceConfig()
        self.state = ServiceState.STOPPED
        
        # Per-channel stats
        self._channel_stats: Dict[int, ChannelStats] = {}
        
        # Software master offsets (per channel)
        self._master_offsets: Dict[int, float] = {}
        
        # Controller management
        self._controllers: Dict[str, BaseController] = {}
        self._active_controllers: List[str] = []
        self._controller_lock = threading.Lock()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Source identifier
        self.source_name: str = "N1700"
        
        # Callbacks
        self.on_reading: Optional[Callable[[int, float, datetime, bool], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_offset: Optional[Callable[[str, int, float, bool], None]] = None
        self.on_state_change: Optional[Callable[[ServiceState], None]] = None
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    def start(self):
        """Start the gauge service in continuous mode."""
        if self.state == ServiceState.RUNNING:
            return
        
        try:
            # Initialize gauge
            self.gauge = N1700(dll_path=self.dll_path)
            num_modules, num_channels = self.gauge.initialize()
            
            if num_channels == 0:
                raise N1700Exception(-1, "No channels detected")
            
            # Initialize per-channel stats
            for i in range(num_channels):
                self._channel_stats[i] = ChannelStats()
                if i not in self._master_offsets:
                    self._master_offsets[i] = 0.0
            
            # Apply filter setting
            self.gauge.set_filter_all(self.config.filter_level)
            
            # Start continuous mode
            self.gauge.start_continuous(callback=self._on_data)
            
            self._set_state(ServiceState.RUNNING)
            
        except Exception as e:
            self._set_state(ServiceState.ERROR)
            if self.on_error:
                self.on_error(e)
            raise
    
    def stop(self):
        """Stop the gauge service."""
        if self.gauge:
            try:
                self.gauge.stop_continuous()
                self.gauge.close()
            except Exception:
                pass
            self.gauge = None
        
        self._set_state(ServiceState.STOPPED)
    
    def _set_state(self, new_state: ServiceState):
        """Update state and notify."""
        self.state = new_state
        if self.on_state_change:
            self.on_state_change(new_state)
    
    @property
    def is_running(self) -> bool:
        return self.state == ServiceState.RUNNING
    
    # =========================================================================
    # CONTINUOUS MODE CALLBACK
    # =========================================================================
    
    def _on_data(self, channel_data: Dict[int, float]):
        """
        Called by N1700 continuous mode when new data arrives.
        This runs in the DLL's callback thread.
        """
        now = timezone.now()
        
        for channel, raw_value in channel_data.items():
            try:
                # Apply master offset
                offset = self._master_offsets.get(channel, 0.0)
                value = raw_value - offset
                
                # Update stats
                stats = self._channel_stats.get(channel)
                if stats:
                    stats.update(value, now)
                
                # Check tolerance
                in_tolerance = True
                measurement = None
                
                feature_id = self.config.feature_map.get(channel)
                if feature_id and self.config.auto_save:
                    measurement = self._save_measurement(feature_id, value, now)
                    if measurement:
                        in_tolerance = measurement.in_tolerance
                
                # Send offset if out of tolerance
                if measurement and self.config.auto_offset and not in_tolerance:
                    self._process_offset(measurement)
                
                # Callback
                if self.on_reading:
                    self.on_reading(channel, value, now, in_tolerance)
                
                # Broadcast to WebSocket
                self._broadcast_reading(channel, value, now, in_tolerance)
                
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
    
    def _broadcast_reading(self, channel: int, value: float, timestamp, in_tolerance: bool):
        """Broadcast reading to WebSocket clients."""
        try:
            from dashboard.consumers import broadcast_reading
            broadcast_reading(channel, value, timestamp, in_tolerance)
        except Exception:
            pass  # Don't let WebSocket errors stop data flow
    
    # =========================================================================
    # FILTER CONTROL
    # =========================================================================
    
    def get_filter(self) -> int:
        """Get current filter level."""
        return self.config.filter_level
    
    def set_filter(self, level: int):
        """
        Set filter level for all channels.
        
        Args:
            level: 0-6 (0=off, 6=64 samples)
        """
        if level < 0 or level > 6:
            raise ValueError("Filter level must be 0-6")
        
        self.config.filter_level = level
        
        if self.gauge and self.is_running:
            self.gauge.set_filter_all(level)
    
    def set_channel_filter(self, channel: int, level: int):
        """Set filter level for a specific channel."""
        if self.gauge and self.is_running:
            self.gauge.set_filter(channel, level)
    
    # =========================================================================
    # MASTERING (SOFTWARE OFFSET)
    # =========================================================================
    
    def master_channel(self, channel: int, master_value: float = 0.0):
        """
        Master (zero) a channel.
        
        Sets the current reading as the reference point.
        
        Args:
            channel: Channel index (0-based)
            master_value: Target value after mastering (default 0.0)
        """
        stats = self._channel_stats.get(channel)
        if stats and stats.last_value is not None:
            # offset = raw - desired
            # so: displayed = raw - offset = desired
            raw = stats.last_value + self._master_offsets.get(channel, 0.0)
            self._master_offsets[channel] = raw - master_value
    
    def master_all(self, master_value: float = 0.0):
        """Master all channels to the same value."""
        for channel in self._channel_stats.keys():
            self.master_channel(channel, master_value)
    
    def clear_master(self, channel: int):
        """Clear master offset for a channel."""
        self._master_offsets[channel] = 0.0
    
    def clear_all_masters(self):
        """Clear all master offsets."""
        for channel in self._master_offsets.keys():
            self._master_offsets[channel] = 0.0
    
    def get_master_offset(self, channel: int) -> float:
        """Get the current master offset for a channel."""
        return self._master_offsets.get(channel, 0.0)
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self, channel: int) -> Optional[ChannelStats]:
        """Get statistics for a channel."""
        return self._channel_stats.get(channel)
    
    def get_all_stats(self) -> Dict[int, ChannelStats]:
        """Get statistics for all channels."""
        return self._channel_stats.copy()
    
    def reset_stats(self, channel: Optional[int] = None):
        """Reset statistics for one or all channels."""
        if channel is not None:
            stats = self._channel_stats.get(channel)
            if stats:
                stats.reset()
        else:
            for stats in self._channel_stats.values():
                stats.reset()
    
    # =========================================================================
    # FEATURE MAPPING
    # =========================================================================
    
    def set_feature(self, channel: int, feature_id: int):
        """Map a channel to a feature for tolerance checking."""
        self.config.feature_map[channel] = feature_id
    
    def clear_feature(self, channel: int):
        """Remove feature mapping for a channel."""
        self.config.feature_map.pop(channel, None)
    
    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================
    
    def _save_measurement(self, feature_id: int, value: float, timestamp) -> Optional[Measurement]:
        """Save measurement to database."""
        try:
            feature = Feature.objects.get(id=feature_id)
            measurement = Measurement.objects.create(
                feature=feature,
                actual=value,
                timestamp=timestamp,
                source=f"{self.source_name}"
            )
            return measurement
        except Feature.DoesNotExist:
            return None
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            return None
    
    # =========================================================================
    # OFFSET PROCESSING
    # =========================================================================
    
    def _process_offset(self, measurement: Measurement):
        """Process offset for an out-of-tolerance measurement."""
        tool_mappings = ToolMapping.objects.filter(
            feature=measurement.feature,
            enabled=True
        ).select_related('controller')
        
        for mapping in tool_mappings:
            offset_value = measurement.deviation * mapping.offset_multiplier
            controller_name = mapping.controller.name
            
            success = self._send_offset(
                controller_name=controller_name,
                tool_number=mapping.tool_number,
                offset_value=offset_value
            )
            
            # Save offset record
            self._save_offset(
                measurement=measurement,
                controller_name=controller_name,
                tool_number=mapping.tool_number,
                offset_value=offset_value,
                success=success
            )
    
    def _send_offset(self, controller_name: str, tool_number: int, offset_value: float) -> bool:
        """Send offset to a controller."""
        with self._controller_lock:
            if controller_name not in self._active_controllers:
                return False
            
            controller = self._controllers.get(controller_name)
            if not controller:
                return False
            
            try:
                success = controller.write_offset(tool_number, offset_value)
                
                if self.on_offset:
                    self.on_offset(controller_name, tool_number, offset_value, success)
                
                # Broadcast to WebSocket
                try:
                    from dashboard.consumers import broadcast_offset
                    broadcast_offset(controller_name, tool_number, offset_value, success)
                except Exception:
                    pass
                
                return success
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
                return False
    
    def _save_offset(self, measurement, controller_name, tool_number, offset_value, success):
        """Save offset record to database."""
        try:
            Offset.objects.create(
                measurement=measurement,
                controller=controller_name,
                tool_number=tool_number,
                offset_value=offset_value,
                applied=success,
                applied_at=timezone.now() if success else None
            )
        except Exception as e:
            if self.on_error:
                self.on_error(e)
    
    # =========================================================================
    # CONTROLLER MANAGEMENT
    # =========================================================================
    
    def add_controller(self, name: str, controller: BaseController) -> bool:
        """Add a controller."""
        with self._controller_lock:
            if name in self._controllers:
                return False
            self._controllers[name] = controller
            return True
    
    def remove_controller(self, name: str) -> bool:
        """Remove a controller."""
        with self._controller_lock:
            if name not in self._controllers:
                return False
            if name in self._active_controllers:
                self._disconnect_controller(name)
            del self._controllers[name]
            return True
    
    def connect_controller(self, name: str) -> bool:
        """Connect a controller."""
        with self._controller_lock:
            if name not in self._controllers:
                return False
            if name in self._active_controllers:
                return True
            
            controller = self._controllers[name]
            try:
                if controller.connect():
                    self._active_controllers.append(name)
                    return True
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
            return False
    
    def disconnect_controller(self, name: str) -> bool:
        """Disconnect a controller."""
        with self._controller_lock:
            return self._disconnect_controller(name)
    
    def _disconnect_controller(self, name: str) -> bool:
        """Internal disconnect (must hold lock)."""
        if name not in self._active_controllers:
            return False
        
        controller = self._controllers[name]
        try:
            controller.disconnect()
        except Exception:
            pass
        
        self._active_controllers.remove(name)
        return True
    
    def list_controllers(self) -> Dict[str, dict]:
        """List all controllers and their status."""
        with self._controller_lock:
            return {
                name: {
                    "type": ctrl.name,
                    "state": ctrl.state.value,
                    "active": name in self._active_controllers
                }
                for name, ctrl in self._controllers.items()
            }
    
    # =========================================================================
    # MANUAL OPERATIONS
    # =========================================================================
    
    def send_offset(self, tool_number: int, offset_value: float, controller_name: Optional[str] = None):
        """Manually send an offset to one or all active controllers."""
        with self._controller_lock:
            targets = [controller_name] if controller_name else self._active_controllers
            
            for name in targets:
                if name in self._controllers and name in self._active_controllers:
                    controller = self._controllers[name]
                    try:
                        success = controller.write_offset(tool_number, offset_value)
                        if self.on_offset:
                            self.on_offset(name, tool_number, offset_value, success)
                    except Exception as e:
                        if self.on_error:
                            self.on_error(e)
    
    def get_channel_info(self) -> List[dict]:
        """Get info for all channels."""
        if not self.gauge:
            return []
        
        info = []
        for i in range(self.gauge.get_num_channels()):
            ch = self.gauge.get_channel(i)
            stats = self._channel_stats.get(i)
            info.append({
                "index": i,
                "display_index": i + 1,  # 1-indexed for display
                "port_type": ch["port_type"].name,
                "filter": ch["filter"],
                "master_offset": self._master_offsets.get(i, 0.0),
                "last_value": stats.last_value if stats else None,
                "count": stats.count if stats else 0,
                "min": stats.min_value if stats else None,
                "max": stats.max_value if stats else None,
            })
        return info


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_service_instance: Optional[GaugeService] = None


def get_service() -> GaugeService:
    """Get the singleton gauge service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GaugeService()
    return _service_instance


def start_service(dll_path: Optional[str] = None) -> GaugeService:
    """Start the gauge service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GaugeService(dll_path=dll_path)
    _service_instance.start()
    return _service_instance


def stop_service():
    """Stop the gauge service."""
    global _service_instance
    if _service_instance:
        _service_instance.stop()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_test_service() -> GaugeService:
    """Create a service with TestController for development."""
    service = GaugeService()
    service.add_controller("test", TestController())
    service.connect_controller("test")
    return service