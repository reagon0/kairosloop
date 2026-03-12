# devices/services.py
"""
Background service for gauge polling and offset management.
Saves measurements to Django database.
"""

import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from dashboard.consumers import broadcast_reading, broadcast_offset
from django.utils import timezone
from .n1700 import N1700, N1700Exception
from .controllers import BaseController, TestController, ControllerState
from .models import GaugeConfig, ChannelConfig, ControllerConfig, ToolMapping
from dmis.models import Feature, Measurement, Offset


class PollingState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class PollingConfig:
    """Configuration for gauge polling."""
    rate_hz: float = 10.0
    channel: int = 0
    auto_offset: bool = False
    auto_save: bool = True  # Save measurements to database
    feature_id: Optional[int] = None  # Feature being measured
    
    @property
    def interval(self) -> float:
        return 1.0 / self.rate_hz


@dataclass 
class PollingStats:
    """Runtime statistics."""
    polls: int = 0
    errors: int = 0
    saves: int = 0
    offsets_sent: int = 0
    last_value: Optional[float] = None
    last_poll: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def update(self, value: float):
        self.polls += 1
        self.last_value = value
        self.last_poll = datetime.now()
        if self.min_value is None or value < self.min_value:
            self.min_value = value
        if self.max_value is None or value > self.max_value:
            self.max_value = value
    
    def reset(self):
        self.polls = 0
        self.errors = 0
        self.saves = 0
        self.offsets_sent = 0
        self.last_value = None
        self.last_poll = None
        self.min_value = None
        self.max_value = None


class GaugePollingService:
    """
    Background service that polls the N1700 gauge.
    Saves measurements to database and sends offsets to controllers.
    """
    
    def __init__(self, gauge: Optional[N1700] = None, dll_path: Optional[str] = None):
        self.gauge = gauge
        self.dll_path = dll_path
        self.config = PollingConfig()
        self.stats = PollingStats()
        self.state = PollingState.STOPPED
        
        # Controller management
        self._controllers: Dict[str, BaseController] = {}
        self._active_controllers: List[str] = []
        self._controller_lock = threading.Lock()
        
        # Thread management
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._config_lock = threading.Lock()
        
        # Source identifier for measurements
        self.source_name: str = "N1700"
        
        # Callbacks
        self.on_reading: Optional[Callable[[float, datetime], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_offset: Optional[Callable[[str, int, float, bool], None]] = None
        self.on_out_of_tolerance: Optional[Callable[[float, float], None]] = None
        self.on_controller_change: Optional[Callable[[str, str], None]] = None
        self.on_measurement_saved: Optional[Callable[[Measurement], None]] = None
    
    # -------------------------------------------------------------------------
    # Controller Management
    # -------------------------------------------------------------------------
    
    def add_controller(self, name: str, controller: BaseController) -> bool:
        with self._controller_lock:
            if name in self._controllers:
                return False
            self._controllers[name] = controller
            self._notify_controller_change(name, "added")
            return True
    
    def remove_controller(self, name: str) -> bool:
        with self._controller_lock:
            if name not in self._controllers:
                return False
            if name in self._active_controllers:
                self._disconnect_controller_unsafe(name)
            del self._controllers[name]
            self._notify_controller_change(name, "removed")
            return True
    
    def connect_controller(self, name: str) -> bool:
        with self._controller_lock:
            if name not in self._controllers:
                return False
            if name in self._active_controllers:
                return True
            controller = self._controllers[name]
            try:
                if controller.connect():
                    self._active_controllers.append(name)
                    self._notify_controller_change(name, "connected")
                    return True
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
            return False
    
    def disconnect_controller(self, name: str) -> bool:
        with self._controller_lock:
            return self._disconnect_controller_unsafe(name)
    
    def _disconnect_controller_unsafe(self, name: str) -> bool:
        if name not in self._active_controllers:
            return False
        controller = self._controllers[name]
        try:
            controller.disconnect()
        except Exception:
            pass
        self._active_controllers.remove(name)
        self._notify_controller_change(name, "disconnected")
        return True
    
    def get_controller(self, name: str) -> Optional[BaseController]:
        return self._controllers.get(name)
    
    def list_controllers(self) -> Dict[str, dict]:
        with self._controller_lock:
            return {
                name: {
                    "type": ctrl.name,
                    "state": ctrl.state.value,
                    "active": name in self._active_controllers
                }
                for name, ctrl in self._controllers.items()
            }
    
    def get_active_controllers(self) -> List[str]:
        with self._controller_lock:
            return self._active_controllers.copy()
    
    def _notify_controller_change(self, name: str, action: str):
        if self.on_controller_change:
            self.on_controller_change(name, action)
    
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    
    @property
    def is_running(self) -> bool:
        return self.state == PollingState.RUNNING
    
    def set_rate(self, hz: float):
        if hz < 1 or hz > 1000:
            raise ValueError("Polling rate must be between 1 and 1000 Hz")
        with self._config_lock:
            self.config.rate_hz = hz
    
    def set_feature(self, feature_id: int):
        """Set which feature we're measuring."""
        with self._config_lock:
            self.config.feature_id = feature_id
    
    def set_channel(self, channel: int):
        with self._config_lock:
            self.config.channel = channel
    
    def enable_auto_offset(self, enabled: bool = True):
        with self._config_lock:
            self.config.auto_offset = enabled
    
    def enable_auto_save(self, enabled: bool = True):
        with self._config_lock:
            self.config.auto_save = enabled
    
    def load_from_database(self, gauge_config_id: int):
        """Load configuration from database."""
        try:
            gauge_config = GaugeConfig.objects.get(id=gauge_config_id)
            self.dll_path = gauge_config.dll_path or None
            self.set_rate(gauge_config.polling_rate_hz)
            self.source_name = gauge_config.name
            
            # Load controllers
            for ctrl_config in ControllerConfig.objects.filter(active=True):
                controller = self._create_controller_from_config(ctrl_config)
                if controller:
                    self.add_controller(ctrl_config.name, controller)
            
            return True
        except GaugeConfig.DoesNotExist:
            return False
    
    def _create_controller_from_config(self, config: ControllerConfig) -> Optional[BaseController]:
        """Create controller instance from database config."""
        if config.controller_type == 'test':
            return TestController(verbose=True)
        # Add other controller types here as implemented
        # elif config.controller_type == 'fanuc':
        #     return FanucController(port=config.port, baudrate=config.baudrate)
        return None
    
    # -------------------------------------------------------------------------
    # Polling Control
    # -------------------------------------------------------------------------
    
    def start(self):
        if self.state == PollingState.RUNNING:
            return
        
        self._stop_event.clear()
        self._pause_event.set()
        self.stats.reset()
        
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        self.state = PollingState.RUNNING
    
    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self.state = PollingState.STOPPED
    
    def pause(self):
        self._pause_event.clear()
        self.state = PollingState.PAUSED
    
    def resume(self):
        self._pause_event.set()
        self.state = PollingState.RUNNING
    
    # -------------------------------------------------------------------------
    # Main Loop
    # -------------------------------------------------------------------------
    
    def _poll_loop(self):
        """Main polling loop."""
        owns_gauge = False
        
        if self.gauge is None:
            try:
                self.gauge = N1700(dll_path=self.dll_path)
                self.gauge.initialize()
                owns_gauge = True
            except N1700Exception as e:
                self.state = PollingState.ERROR
                if self.on_error:
                    self.on_error(e)
                return
        
        try:
            while not self._stop_event.is_set():
                self._pause_event.wait()
                
                if self._stop_event.is_set():
                    break
                
                # Get config
                with self._config_lock:
                    interval = self.config.interval
                    channel = self.config.channel
                    feature_id = self.config.feature_id
                    auto_offset = self.config.auto_offset
                    auto_save = self.config.auto_save
                
                # Poll
                try:
                    value = self.gauge.poll_data(channel)
                    now = timezone.now()
                    self.stats.update(value)
                    
                    # Callback
                    if self.on_reading:
                        self.on_reading(value, now)
                    
                    # Save to database
                    measurement = None
                    if auto_save and feature_id:
                        measurement = self._save_measurement(feature_id, value, now)
                    
                    # Check tolerance and send offset
                    if measurement and auto_offset:
                        self._check_and_send_offset(measurement)
                    
                    # Broadcast to WebSocket clients
                    try:
                        from dashboard.consumers import broadcast_reading
                        in_tol = True
                        if measurement:
                            in_tol = measurement.in_tolerance
                        broadcast_reading(channel, value, now, in_tol)
                    except Exception:
                        pass  # Don't let WebSocket errors stop polling
                
                except N1700Exception as e:
                    self.stats.errors += 1
                    if self.on_error:
                        self.on_error(e)
                except Exception as e:
                    self.stats.errors += 1
                    if self.on_error:
                        self.on_error(e)
                
                time.sleep(interval)
        
        finally:
            if owns_gauge and self.gauge:
                self.gauge.close()
                self.gauge = None
    
    # -------------------------------------------------------------------------
    # Database Operations
    # -------------------------------------------------------------------------
    
    def _save_measurement(self, feature_id: int, value: float, timestamp) -> Optional[Measurement]:
        """Save measurement to database."""
        try:
            feature = Feature.objects.get(id=feature_id)
            measurement = Measurement.objects.create(
                feature=feature,
                actual=value,
                timestamp=timestamp,
                source=f"{self.source_name}:Ch{self.config.channel}"
            )
            self.stats.saves += 1
            
            if self.on_measurement_saved:
                self.on_measurement_saved(measurement)
            
            return measurement
        except Feature.DoesNotExist:
            return None
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            return None
    
    def _check_and_send_offset(self, measurement: Measurement):
        """Check if measurement is out of tolerance and send offset."""
        if measurement.in_tolerance:
            return
        
        # Out of tolerance - notify
        if self.on_out_of_tolerance:
            self.on_out_of_tolerance(measurement.actual, measurement.deviation)
        
        # Find tool mappings for this feature
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
    
    def _save_offset(
        self,
        measurement: Measurement,
        controller_name: str,
        tool_number: int,
        offset_value: float,
        success: bool
    ):
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
            if success:
                self.stats.offsets_sent += 1
        except Exception as e:
            if self.on_error:
                self.on_error(e)
    
    def _send_offset(self, controller_name: str, tool_number: int, offset_value: float) -> bool:
        """Send offset to a specific controller."""
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
                
                # Broadcast to WebSocket clients
                try:
                    from dashboard.consumers import broadcast_offset
                    broadcast_offset(controller_name, tool_number, offset_value, success)
                except Exception:
                    pass  # Don't let WebSocket errors stop offset sending
                
                return success
            except Exception as e:
                if self.on_error:
                    self.on_error(e)
                return False
    
    # -------------------------------------------------------------------------
    # Manual Operations
    # -------------------------------------------------------------------------
    
    def send_offset(self, tool_number: int, offset_value: float, controller_name: Optional[str] = None):
        """Manually send offset to one or all active controllers."""
        with self._controller_lock:
            targets = [controller_name] if controller_name else self._active_controllers
            
            for name in targets:
                if name not in self._controllers:
                    continue
                if name not in self._active_controllers:
                    continue
                
                controller = self._controllers[name]
                try:
                    success = controller.write_offset(tool_number, offset_value)
                    if self.on_offset:
                        self.on_offset(name, tool_number, offset_value, success)
                except Exception as e:
                    if self.on_error:
                        self.on_error(e)
    
    def take_single_measurement(self, feature_id: int, channel: Optional[int] = None) -> Optional[Measurement]:
        """Take and save a single measurement (doesn't require polling to be running)."""
        if self.gauge is None:
            return None
        
        ch = channel if channel is not None else self.config.channel
        try:
            value = self.gauge.poll_data(ch)
            return self._save_measurement(feature_id, value, timezone.now())
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            return None


# -------------------------------------------------------------------------
# Convenience Functions
# -------------------------------------------------------------------------

def poll_once(channel: int = 0, dll_path: Optional[str] = None) -> float:
    """Take a single gauge reading (no database)."""
    with N1700(dll_path=dll_path) as gauge:
        gauge.initialize()
        return gauge.poll_data(channel)


def create_test_service(rate_hz: float = 10.0, feature_id: Optional[int] = None) -> GaugePollingService:
    """Create a service with TestController for development."""
    service = GaugePollingService()
    service.add_controller("test", TestController())
    service.connect_controller("test")
    service.set_rate(rate_hz)
    if feature_id:
        service.set_feature(feature_id)
    return service