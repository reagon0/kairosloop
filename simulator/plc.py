# simulator/plc.py
"""
Simulated PLC/CNC for testing.

This simulates the behavior of a real CNC machine:
- Maintains tool offset registers
- Tracks machine state (RUNNING, ALARM, etc.)
- Counts parts
- Responds to signals from KairosLoop
- Sends signals back (CYCLE_COMPLETE, etc.)
- Triggers measurement after each cycle (when simulation enabled)
"""

import time
import threading
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime

from django.utils import timezone

from controller.drivers import MachineState, Signal

logger = logging.getLogger(__name__)


class TestPLC:
    """
    Simulates CNC/PLC hardware for testing.
    
    Usage:
        plc = TestPLC()
        plc.start()
        
        # Simulate operator starting program
        plc.operator_start()
        
        # PLC will emit CYCLE_COMPLETE signals
        # KairosLoop captures measurements
        # Sends offsets back to PLC
        
        plc.stop()
    """
    
    def __init__(self, cycle_time: float = 5.0):
        # Configuration
        self.cycle_time = cycle_time  # Seconds per part
        
        # Machine state
        self._state = MachineState.IDLE
        self._alarm_active = False
        self._alarm_message = ''
        self._warning_active = False
        self._warning_message = ''
        
        # Part tracking
        self._part_count_today = 0
        self._part_count_total = 0
        self._cycle_active = False
        self._cycle_start_time: Optional[datetime] = None
        
        # Tool offset registers (simulates CNC memory)
        # {tool_number: {axis: offset_value}}
        self._tool_offsets: Dict[int, Dict[str, float]] = {}
        
        # Tool wear accumulator (tracks total offset applied)
        self._tool_wear: Dict[int, float] = {}
        
        # Initialize default tools
        for t in range(1, 11):
            self._tool_offsets[t] = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
            self._tool_wear[t] = 0.0
        
        # Signal callbacks
        self._signal_handlers: List[Callable] = []
        
        # Auto-cycle thread
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # WebSocket broadcast callback
        self._on_state_change: Optional[Callable] = None
        
        # Simulation mode - auto-measure after each cycle
        self._simulation_enabled = False
        self._tool_wear_sim = None
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def state(self) -> MachineState:
        return self._state
    
    @property
    def is_running(self) -> bool:
        return self._state == MachineState.RUNNING
    
    @property
    def simulation_enabled(self) -> bool:
        return self._simulation_enabled
    
    # =========================================================================
    # SIMULATION CONTROL
    # =========================================================================
    
    def enable_simulation(self, tool_wear_sim: 'ToolWearSimulation' = None):
        """
        Enable full simulation mode.
        
        When enabled, each CYCLE_COMPLETE will:
        1. Apply tool wear
        2. Simulate gauge readings
        3. Call capture_measurement()
        """
        if tool_wear_sim is None:
            from simulator.tool_wear import get_tool_wear_simulation
            tool_wear_sim = get_tool_wear_simulation()
        
        self._tool_wear_sim = tool_wear_sim
        self._simulation_enabled = True
        logger.info("[TestPLC] Simulation mode ENABLED")
    
    def disable_simulation(self):
        """Disable simulation mode."""
        self._simulation_enabled = False
        logger.info("[TestPLC] Simulation mode DISABLED")
    
    # =========================================================================
    # RECEIVE COMMANDS FROM DRIVER (KairosLoop → PLC)
    # =========================================================================
    
    def write_offset(self, tool: int, axis: str, value: float):
        """Receive offset adjustment from KairosLoop."""
        if tool not in self._tool_offsets:
            self._tool_offsets[tool] = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        
        # Apply offset (additive)
        self._tool_offsets[tool][axis] += value
        
        # Track wear (absolute accumulation)
        if tool not in self._tool_wear:
            self._tool_wear[tool] = 0.0
        self._tool_wear[tool] += abs(value)
        
        logger.info(
            f"[TestPLC] T{tool} {axis}-offset: {self._tool_offsets[tool][axis]:+.4f} "
            f"(total wear: {self._tool_wear[tool]:.4f})"
        )
        
        self._broadcast_state()
    
    def read_offset(self, tool: int, axis: str) -> float:
        """Read current offset value."""
        if tool not in self._tool_offsets:
            return 0.0
        return self._tool_offsets[tool].get(axis, 0.0)
    
    def receive_alarm(self, message: str):
        """Receive ALARM signal from KairosLoop."""
        self._state = MachineState.ALARM
        self._alarm_active = True
        self._alarm_message = message
        self._cycle_active = False
        
        logger.warning(f"[TestPLC] ALARM: {message}")
        self._broadcast_state()
        self._emit_signal(Signal.STATE_CHANGE, {'state': self._state.value})
    
    def receive_warning(self, message: str):
        """Receive WARNING signal from KairosLoop."""
        self._warning_active = True
        self._warning_message = message
        
        logger.info(f"[TestPLC] WARNING: {message}")
        self._broadcast_state()
    
    def receive_tool_change_request(self, tool: int):
        """Receive tool change request from KairosLoop."""
        self._state = MachineState.TOOL_CHANGE
        self._cycle_active = False
        
        logger.info(f"[TestPLC] Tool change requested: T{tool}")
        self._broadcast_state()
        self._emit_signal(Signal.STATE_CHANGE, {'state': self._state.value, 'tool': tool})
    
    # =========================================================================
    # OPERATOR ACTIONS (Dashboard → PLC)
    # =========================================================================
    
    def operator_start(self):
        """Operator presses START."""
        if self._state in (MachineState.IDLE, MachineState.ALARM):
            if self._alarm_active:
                logger.warning("[TestPLC] Cannot start - alarm active")
                return False
            
            self._state = MachineState.RUNNING
            logger.info("[TestPLC] Program STARTED")
            self._broadcast_state()
            self._emit_signal(Signal.PROGRAM_START, {})
            return True
        return False
    
    def operator_stop(self):
        """Operator presses STOP."""
        self._state = MachineState.IDLE
        self._cycle_active = False
        
        logger.info("[TestPLC] Program STOPPED")
        self._broadcast_state()
        self._emit_signal(Signal.PROGRAM_STOP, {})
    
    def operator_ack_alarm(self):
        """Operator acknowledges alarm."""
        if self._alarm_active:
            self._alarm_active = False
            self._alarm_message = ''
            self._state = MachineState.IDLE
            
            logger.info("[TestPLC] Alarm ACKNOWLEDGED")
            self._broadcast_state()
            self._emit_signal(Signal.ALARM_ACK, {})
            return True
        return False
    
    def operator_clear_warning(self):
        """Operator clears warning."""
        self._warning_active = False
        self._warning_message = ''
        self._broadcast_state()
    
    def operator_change_tool(self, tool: int):
        """Operator changes a tool (resets wear and offsets)."""
        # Reset offset for this tool
        self._tool_offsets[tool] = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self._tool_wear[tool] = 0.0
        
        # Reset simulated wear too
        if self._tool_wear_sim:
            self._tool_wear_sim.reset_tool(tool)
        
        # Return to IDLE if in TOOL_CHANGE state
        if self._state == MachineState.TOOL_CHANGE:
            self._state = MachineState.IDLE
        
        logger.info(f"[TestPLC] Tool T{tool} CHANGED - offsets and wear reset")
        self._broadcast_state()
        self._emit_signal(Signal.TOOL_CHANGED, {'tool': tool})
    
    def operator_reset_part_count(self):
        """Reset daily part count."""
        self._part_count_today = 0
        self._broadcast_state()
    
    # =========================================================================
    # CYCLE SIMULATION
    # =========================================================================
    
    def simulate_cycle(self):
        """Simulate a single machining cycle."""
        if self._state != MachineState.RUNNING:
            logger.warning("[TestPLC] Cannot cycle - not running")
            return
        
        self._cycle_active = True
        self._cycle_start_time = timezone.now()
        
        # Simulate machining time
        time.sleep(self.cycle_time)
        
        # Check if still running (could have been stopped)
        if self._state == MachineState.RUNNING:
            self._cycle_active = False
            self._part_count_today += 1
            self._part_count_total += 1
            
            logger.info(f"[TestPLC] CYCLE COMPLETE - Part #{self._part_count_today}")
            self._broadcast_state()
            self._emit_signal(Signal.CYCLE_COMPLETE, {
                'part_count': self._part_count_today,
            })
            
            # If simulation enabled, measure the "part"
            if self._simulation_enabled:
                self._simulate_measurement()
    
    def _simulate_measurement(self):
        """Simulate gauge measurement after cycle complete."""
        try:
            from simulator.gauge import simulate_gauge_readings
            from measurement.capture import capture_measurement
            
            # Apply tool wear for this cycle
            if self._tool_wear_sim:
                self._tool_wear_sim.cycle_all()
            
            # Get simulated gauge readings
            readings = simulate_gauge_readings(self, self._tool_wear_sim)
            
            # Feed to KairosLoop
            result = capture_measurement(
                channel_values=readings,
                source='simulator'
            )
            
            logger.info(
                f"[TestPLC] Simulated measurement: "
                f"pass={result.all_pass}, features={len(result.feature_results)}"
            )
            
        except Exception as e:
            logger.exception("[TestPLC] Error in simulated measurement")
    
    def start(self):
        """Start auto-cycle thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._cycle_loop, daemon=True)
        self._thread.start()
        logger.info("[TestPLC] Auto-cycle thread started")
    
    def stop(self):
        """Stop auto-cycle thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("[TestPLC] Auto-cycle thread stopped")
    
    def _cycle_loop(self):
        """Background thread that runs cycles when in RUNNING state."""
        while self._running:
            if self._state == MachineState.RUNNING and not self._cycle_active:
                self.simulate_cycle()
            else:
                time.sleep(0.1)
    
    # =========================================================================
    # STATE ACCESS
    # =========================================================================
    
    def get_state(self) -> dict:
        """Get current state for dashboard."""
        state = {
            'state': self._state.value,
            'alarm_active': self._alarm_active,
            'alarm_message': self._alarm_message,
            'warning_active': self._warning_active,
            'warning_message': self._warning_message,
            'part_count_today': self._part_count_today,
            'part_count_total': self._part_count_total,
            'cycle_active': self._cycle_active,
            'cycle_time': self.cycle_time,
            'tool_offsets': {str(k): v for k, v in self._tool_offsets.items()},
            'tool_wear': {str(k): v for k, v in self._tool_wear.items()},
            'simulation_enabled': self._simulation_enabled,
        }
        
        # Include simulated wear if available
        if self._tool_wear_sim:
            state['simulated_wear'] = self._tool_wear_sim.get_state()
        
        return state
    
    # =========================================================================
    # SIGNAL HANDLING
    # =========================================================================
    
    def on_signal(self, handler: Callable):
        """Register a handler for signals from PLC."""
        self._signal_handlers.append(handler)
    
    def _emit_signal(self, signal: Signal, data: dict):
        """Emit signal to all registered handlers."""
        for handler in self._signal_handlers:
            try:
                handler(signal, data)
            except Exception as e:
                logger.exception(f"Error in PLC signal handler")
    
    def set_state_callback(self, callback: Callable):
        """Set callback for state changes (for WebSocket broadcast)."""
        self._on_state_change = callback
    
    def _broadcast_state(self):
        """Broadcast state change."""
        if self._on_state_change:
            try:
                self._on_state_change(self.get_state())
            except Exception as e:
                logger.exception("Error broadcasting PLC state")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_test_plc: Optional[TestPLC] = None


def get_test_plc() -> TestPLC:
    """Get the singleton TestPLC instance."""
    global _test_plc
    if _test_plc is None:
        _test_plc = TestPLC()
    return _test_plc


def start_test_plc(cycle_time: float = 5.0) -> TestPLC:
    """Start the TestPLC with auto-cycling."""
    global _test_plc
    
    if _test_plc is None:
        _test_plc = TestPLC(cycle_time=cycle_time)
    
    _test_plc.start()
    return _test_plc


def stop_test_plc():
    """Stop the TestPLC."""
    global _test_plc
    if _test_plc:
        _test_plc.stop()


def start_simulation(cycle_time: float = 3.0) -> TestPLC:
    """
    Start the full simulation loop.
    
    Convenience function that:
    1. Gets/creates TestPLC
    2. Enables simulation mode (with tool wear)
    3. Starts the cycle thread
    
    Usage:
        plc = start_simulation(cycle_time=3.0)
        plc.operator_start()  # Begin running
    """
    global _test_plc
    
    if _test_plc is None:
        _test_plc = TestPLC(cycle_time=cycle_time)
    
    _test_plc.enable_simulation()
    _test_plc.start()
    
    return _test_plc