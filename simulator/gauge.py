# simulator/gauge.py
"""
Simulated gauge readings based on tool wear and compensation.

Two opposing probes measure an OD. As Tool 1 wears, the diameter shrinks.
Compensation offsets push it back.

    reading = nominal - wear + offset + random_variation
"""

import random
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from simulator.plc import TestPLC
    from simulator.tool_wear import ToolWearSimulation


# Two opposing probes for OD measurement
CHANNEL_CONFIG = {
    0: {
        'name': 'OD Probe Left',
        'nominal': 12.700,
        'tool': 1,
        'axis': 'X',
        'wear_direction': -1,
        'variation': 0.0005,
    },
    1: {
        'name': 'OD Probe Right',
        'nominal': 12.700,
        'tool': None,
        'axis': None,
        'wear_direction': 0,
        'variation': 0.0005,
    },
}


def simulate_gauge_readings(
    plc: 'TestPLC',
    tool_wear: 'ToolWearSimulation'
) -> Dict[int, float]:
    """
    Simulate what the gauge would read after machining.

    Each probe reads:
        nominal + (wear * wear_direction) + offset + random_variation

    Two probes added together = diameter.
    """
    readings = {}

    for channel, config in CHANNEL_CONFIG.items():
        nominal = config['nominal']
        variation = random.gauss(0, config['variation'])

        tool_effect = 0.0
        if config['tool'] is not None:
            tool = config['tool']
            axis = config['axis']
            wear = tool_wear.get_wear(tool) if tool_wear else 0.0
            offset = plc.read_offset(tool, axis)
            tool_effect = (wear * config['wear_direction']) + offset

        readings[channel] = nominal + tool_effect + variation

    return readings


def get_channel_config() -> Dict[int, dict]:
    """Get channel configuration."""
    return CHANNEL_CONFIG.copy()