# compensation/models.py
"""
Compensation layer models.

CompensationRule: Links a Feature to a Controller tool offset with trigger logic.
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
    One rule = one feature → one tool offset relationship.
    
    Defines when and how to compensate based on measurement deviation.
    """
    
    # === Links ===
    feature = models.ForeignKey(
        'measurement.Feature',
        on_delete=models.CASCADE,
        related_name='compensation_rules',
        help_text="Feature to monitor for compensation"
    )
    controller = models.ForeignKey(
        'controller.ControllerConfig',
        on_delete=models.CASCADE,
        related_name='compensation_rules',
        help_text="Controller to send offset adjustments"
    )
    
    # === Tool Mapping ===
    tool_number = models.IntegerField(
        help_text="Tool number in CNC (e.g., 1 for T01)"
    )
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
    wear_limit = models.FloatField(
        default=0.050,
        help_text="Alert/stop when accumulated offset reaches this"
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
    accumulated_offset = models.FloatField(
        default=0,
        help_text="Running total of all offset adjustments"
    )
    last_adjustment = models.FloatField(
        default=0,
        help_text="Most recent offset adjustment"
    )
    last_adjustment_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When last adjustment was made"
    )
    
    # === Metadata ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compensation Rule"
        verbose_name_plural = "Compensation Rules"
        unique_together = ['feature', 'controller', 'tool_number']
        ordering = ['feature__name', 'tool_number']
    
    def __str__(self):
        return f"{self.feature.name} → T{self.tool_number} ({self.controller.name})"
    
    @property
    def wear_percentage(self) -> float:
        """Percentage of wear limit used."""
        if self.wear_limit == 0:
            return 0
        return abs(self.accumulated_offset) / self.wear_limit * 100
    
    @property
    def wear_status(self) -> str:
        """Status based on wear percentage."""
        pct = self.wear_percentage
        if pct >= 100:
            return 'critical'
        elif pct >= 80:
            return 'warning'
        else:
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
        
        # Check wear limit
        new_accumulated = abs(self.accumulated_offset) + abs(raw_offset)
        if new_accumulated > self.wear_limit:
            if self.wear_limit_action == WearLimitAction.STOP:
                result['status'] = CompensationStatus.BLOCKED
                result['reason'] = f"Wear limit {self.wear_limit} exceeded"
                return result
            elif self.wear_limit_action == WearLimitAction.ALERT:
                # Still apply, but flag it
                result['reason'] = f"Wear limit warning: {new_accumulated:.4f} / {self.wear_limit}"
        
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
    
    def apply_offset(self, offset_value: float):
        """Update accumulated offset after applying."""
        self.accumulated_offset += offset_value
        self.last_adjustment = offset_value
        self.last_adjustment_at = timezone.now()
        self.save(update_fields=['accumulated_offset', 'last_adjustment', 'last_adjustment_at', 'updated_at'])
    
    def reset_accumulated(self):
        """Reset accumulated offset (e.g., after tool change)."""
        self.accumulated_offset = 0
        self.last_adjustment = 0
        self.save(update_fields=['accumulated_offset', 'last_adjustment', 'updated_at'])


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
        return f"{self.rule.feature.name} T{self.rule.tool_number}: {self.offset_applied:+.4f} [{self.status}]"
    
    @classmethod
    def create_from_calculation(
        cls,
        rule: CompensationRule,
        measurement,
        deviation: float,
        calc_result: dict
    ) -> 'CompensationEvent':
        """Create event from calculation result."""
        accumulated_before = rule.accumulated_offset
        
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
            accumulated_after=accumulated_before + calc_result['offset_to_apply'],
            status=status,
            reason=calc_result['reason'],
        )
        
        return event
