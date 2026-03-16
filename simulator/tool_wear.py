# simulator/tool_wear.py
"""
Tool wear simulation.

Simulates gradual wear on Tool 1. As it wears, OD parts come out
undersized. KairosLoop compensates until wear limit is reached.
"""

import random
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """Configuration for a single tool."""
    wear_rate: float
    variation: float = 0.2
    wear_limit: float = 0.1


class ToolWearSimulation:

    def __init__(self):
        self._tools: Dict[int, ToolConfig] = {}
        self._wear: Dict[int, float] = {}
        self._cycle_count: Dict[int, int] = {}
        self._on_change: Optional[Callable] = None

    def configure_tool(self, tool: int, wear_rate: float, variation: float = 0.2, wear_limit: float = 0.1):
        self._tools[tool] = ToolConfig(wear_rate=wear_rate, variation=variation, wear_limit=wear_limit)
        if tool not in self._wear:
            self._wear[tool] = 0.0
            self._cycle_count[tool] = 0
        logger.info(f"Tool T{tool} configured: rate={wear_rate}, limit={wear_limit}")

    def cycle(self, tool: int) -> float:
        config = self._tools.get(tool)
        if config is None:
            self.configure_tool(tool, wear_rate=0.0005)
            config = self._tools[tool]

        var_factor = 1.0 + random.uniform(-config.variation, config.variation)
        wear_this_cycle = config.wear_rate * var_factor

        self._wear[tool] = self._wear.get(tool, 0.0) + wear_this_cycle
        self._cycle_count[tool] = self._cycle_count.get(tool, 0) + 1

        self._notify_change()
        return self._wear[tool]

    def cycle_all(self):
        for tool in self._tools.keys():
            self.cycle(tool)

    def get_wear(self, tool: int) -> float:
        return self._wear.get(tool, 0.0)

    def get_cycle_count(self, tool: int) -> int:
        return self._cycle_count.get(tool, 0)

    def get_wear_percentage(self, tool: int) -> float:
        config = self._tools.get(tool)
        if config is None or config.wear_limit == 0:
            return 0.0
        return (self._wear.get(tool, 0.0) / config.wear_limit) * 100

    def is_worn(self, tool: int) -> bool:
        config = self._tools.get(tool)
        if config is None:
            return False
        return self._wear.get(tool, 0.0) >= config.wear_limit

    def set_wear_rate(self, tool: int, rate: float):
        if tool in self._tools:
            self._tools[tool].wear_rate = rate
            self._notify_change()
        else:
            self.configure_tool(tool, wear_rate=rate)

    def induce_wear(self, tool: int, amount: float):
        self._wear[tool] = self._wear.get(tool, 0.0) + amount
        logger.info(f"Tool T{tool} induced wear +{amount}, total: {self._wear[tool]:.4f}")
        self._notify_change()

    def reset_tool(self, tool: int):
        self._wear[tool] = 0.0
        self._cycle_count[tool] = 0
        logger.info(f"Tool T{tool} reset (tool change)")
        self._notify_change()

    def reset_all(self):
        for tool in list(self._wear.keys()):
            self.reset_tool(tool)

    def get_state(self) -> dict:
        tools = {}
        for tool, config in self._tools.items():
            tools[str(tool)] = {
                'wear': self._wear.get(tool, 0.0),
                'wear_rate': config.wear_rate,
                'wear_limit': config.wear_limit,
                'wear_percentage': self.get_wear_percentage(tool),
                'cycle_count': self._cycle_count.get(tool, 0),
                'is_worn': self.is_worn(tool),
            }
        return {
            'tools': tools,
            'total_cycles': sum(self._cycle_count.values()),
        }

    def set_change_callback(self, callback: Callable):
        self._on_change = callback

    def _notify_change(self):
        if self._on_change:
            try:
                self._on_change(self.get_state())
            except Exception as e:
                logger.exception("Error in wear simulation callback")


# Singleton — Tool 1 only
_instance: Optional[ToolWearSimulation] = None


def get_tool_wear_simulation() -> ToolWearSimulation:
    global _instance
    if _instance is None:
        _instance = ToolWearSimulation()
        _instance.configure_tool(1, wear_rate=0.0005, wear_limit=0.10)
    return _instance


def reset_tool_wear_simulation():
    global _instance
    if _instance:
        _instance.reset_all()
    _instance = None