# compensation/models.py
"""
Compensation layer models.

CompensationRule: Links a Feature to a ToolAssignment with trigger logic.
CompensationEvent: Log of every compensation decision.
"""

from django.db import models
from django.utils import timezone


class TriggerMode(models.TextChoices):
    """How compensation is triggered."""
    THRESHOLD = 'THR', 'Threshold (compensate when deviation exceeds)'
    EVERY_CYCLE = 'ALL', 'Every Cycle (always compensate)'
    AVERAGE_N = 'AVG', 'Average N samples before compensating'


class WearLimitAction(models.TextChoices):
    """What to do when wear limit is reached."""
    ALERT = 'ALERT', 'Alert operator'
    STOP = 'STOP', 'Stop compensation'
    TOOL_CHANGE = 'TOOL', 'Request tool change'


class CompensationStatus(models.TextChoices):
    """Status of a compensation event."""
    APPLIED = 'APPLIED', 'Applied'
    SKIPPED = 'SKIPPED', 'Skipped (below threshold)'
    CLAMPED = 'CLAMPED', 'Clamped (exceeded max per cycle)'
    BLOCKED = 'BLOCKED', 'Blocked (wear limit reached)'
    ERROR = 'ERROR', 'Error'


class CompensationRule(models.Model):
    """
    One rule = one feature → one tool relationship.
    
    Defines when and how to compensate based on measurement deviation.
    """
    
    # === Links ===
    feature = models.ForeignKey(
        'measurement.Feature',
        on_delete=models.CASCADE,
        related_name='compensation_rules',
        help_text="Feature to monitor for compensation"
    )
    
    tool_assignment = models.ForeignKey(
        'tooling.ToolAssignment',
        on_delete=models.CASCADE,
        related_name='compensation_rules',
        help_text="Tool assignment to send offsets to"
    )
    
    # === Offset Settings ===
    offset_register = models.CharField(
        max_length=20,
        blank=True,
        help_text="Offset register if different from tool (e.g., 'D01', 'H01')"
    )
    offset_axis = models.CharField(
        max_length=1,
        default='X',
        choices=[('X', 'X'), ('Y', 'Y'), ('Z', 'Z')],
        help_text="Axis this tool cuts on"
    )
    offset_direction = models.FloatField(
        default=-1.0,
        help_text="Multiplier: -1 = compensate (most common), +1 = amplify"
    )
    
    # === Trigger Logic ===
    trigger_mode = models.CharField(
        max_length=3,
        choices=TriggerMode.choices,
        default=TriggerMode.THRESHOLD,
        help_text="When to trigger compensation"
    )
    trigger_threshold = models.FloatField(
        default=0.005,
        help_text="Compensate when |deviation| exceeds this (for THRESHOLD mode)"
    )
    sample_count = models.IntegerField(
        default=1,
        help_text="Number of samples to average (for AVG mode)"
    )
    
    # === Safety Limits ===
    max_per_cycle = models.FloatField(
        default=0.010,
        help_text="Maximum offset change per cycle (safety cap)"
    )
    warning_threshold = models.FloatField(
        default=0.8,
        help_text="Warn when accumulated offset reaches this fraction of tool limit (0.0-1.0)"
    )
    wear_limit_action = models.CharField(
        max_length=5,
        choices=WearLimitAction.choices,
        default=WearLimitAction.ALERT,
        help_text="Action when wear limit is reached"
    )
    
    # === State ===
    active = models.BooleanField(
        default=True,
        help_text="Enable/disable this compensation rule"
    )
    
    # === Metadata ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compensation Rule"
        verbose_name_plural = "Compensation Rules"
        ordering = ['feature__name']
    
    def __str__(self):
        return f"{self.feature.name} → T{self.tool_assignment.tool_position} ({self.tool_assignment.controller.name})"
    
    @property
    def tool_position(self) -> int:
        """Get tool position from assignment."""
        return self.tool_assignment.tool_position
    
    @property
    def controller(self):
        """Get controller from assignment."""
        return self.tool_assignment.controller
    
    @property
    def wear_percentage(self) -> float:
        """Percentage of tool limit used."""
        return self.tool_assignment.usage_percentage
    
    @property
    def wear_status(self) -> str:
        """Status based on wear percentage."""
        pct = self.wear_percentage
        if pct >= 100:
            return 'critical'
        elif pct >= (self.warning_threshold * 100):
            return 'warning'
        return 'ok'
    
    def calculate_offset(self, deviation: float) -> dict:
        """
        Calculate offset based on deviation and rule settings.
        
        Returns dict with:
            - should_compensate: bool
            - offset_calculated: float (raw)
            - offset_to_apply: float (after clamping)
            - status: CompensationStatus
            - reason: str
        """
        result = {
            'should_compensate': False,
            'offset_calculated': 0,
            'offset_to_apply': 0,
            'status': CompensationStatus.SKIPPED,
            'reason': '',
        }
        
        # Check trigger condition
        if self.trigger_mode == TriggerMode.THRESHOLD:
            if abs(deviation) <= self.trigger_threshold:
                result['reason'] = f"Deviation {deviation:+.4f} within threshold ±{self.trigger_threshold}"
                return result
        
        # Calculate raw offset
        raw_offset = deviation * self.offset_direction
        result['offset_calculated'] = raw_offset
        
        # Clamp to max per cycle
        if abs(raw_offset) > self.max_per_cycle:
            clamped = self.max_per_cycle if raw_offset > 0 else -self.max_per_cycle
            result['offset_to_apply'] = clamped
            result['status'] = CompensationStatus.CLAMPED
            result['reason'] = f"Clamped from {raw_offset:+.4f} to {clamped:+.4f}"
        else:
            result['offset_to_apply'] = raw_offset
            result['status'] = CompensationStatus.APPLIED
            result['reason'] = f"Offset {raw_offset:+.4f}"
        
        result['should_compensate'] = True
        return result


class CompensationEvent(models.Model):
    """
    Log of every compensation decision.
    
    Records what happened for each measurement cycle.
    """
    
    rule = models.ForeignKey(
        CompensationRule,
        on_delete=models.CASCADE,
        related_name='events'
    )
    measurement = models.ForeignKey(
        'measurement.Measurement',
        on_delete=models.CASCADE,
        related_name='compensation_events'
    )
    
    # What came in
    deviation_in = models.FloatField(
        help_text="Deviation from measurement"
    )
    
    # What was calculated
    offset_calculated = models.FloatField(
        help_text="Raw offset before safety clamps"
    )
    offset_applied = models.FloatField(
        help_text="Actual offset sent to controller"
    )
    
    # Accumulated tracking
    accumulated_before = models.FloatField(
        help_text="Accumulated offset before this event"
    )
    accumulated_after = models.FloatField(
        help_text="Accumulated offset after this event"
    )
    
    # Result
    status = models.CharField(
        max_length=10,
        choices=CompensationStatus.choices,
        help_text="What happened"
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Explanation of decision"
    )
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Compensation Event"
        verbose_name_plural = "Compensation Events"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['rule', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.rule.feature.name} T{self.rule.tool_position}: {self.offset_applied:+.4f} [{self.status}]"
    
    @classmethod
    def create_from_calculation(
        cls,
        rule: CompensationRule,
        measurement,
        deviation: float,
        calc_result: dict
    ) -> 'CompensationEvent':
        """Create event from calculation result."""
        accumulated_before = abs(rule.tool_assignment.accumulated_offset)
        
        # Handle status - could be enum or string
        status = calc_result['status']
        if hasattr(status, 'value'):
            status = status.value  # Convert enum to string
        
        event = cls.objects.create(
            rule=rule,
            measurement=measurement,
            deviation_in=deviation,
            offset_calculated=calc_result['offset_calculated'],
            offset_applied=calc_result['offset_to_apply'],
            accumulated_before=accumulated_before,
            accumulated_after=accumulated_before + abs(calc_result['offset_to_apply']),
            status=status,
            reason=calc_result['reason'],
        )
        
        return event