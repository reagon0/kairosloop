# dmis/models.py
"""
DMIS-aligned measurement models with dynamic formula editor support.

Supports configurable channel combinations for different measurement types:
- Single input: TIR, runout, single-probe deviation
- Multi-input: Opposing probe diameter, differential, average, complex formulas
- Formula: Custom expression using inputs A, B, C... with operators
"""

from django.db import models
from django.utils import timezone
from typing import Dict, Optional, List
import math
import re


# =============================================================================
# CHOICES
# =============================================================================

class ToleranceMode(models.TextChoices):
    """How tolerance is evaluated."""
    BILATERAL = 'BI', 'Bilateral (± from nominal)'
    UNILATERAL_POS = 'UNI_P', 'Unilateral Positive (nominal to +upper)'
    UNILATERAL_NEG = 'UNI_N', 'Unilateral Negative (nominal to -lower)'
    LIMIT = 'LIM', 'Limit Only (0 to limit, e.g., TIR)'


class FeatureType(models.TextChoices):
    """GD&T feature types for reporting/documentation."""
    DIAMETER = 'DIA', 'Diameter'
    RADIUS = 'RAD', 'Radius'
    LENGTH = 'LEN', 'Length'
    POSITION = 'POS', 'Position'
    TIR = 'TIR', 'TIR (Total Indicator Reading)'
    RUNOUT = 'RUN', 'Runout'
    FLATNESS = 'FLT', 'Flatness'
    PERPENDICULARITY = 'PER', 'Perpendicularity'
    PARALLELISM = 'PAR', 'Parallelism'
    CONCENTRICITY = 'CON', 'Concentricity'
    TAPER = 'TAP', 'Taper'
    DEVIATION = 'DEV', 'Deviation (Generic)'


class Unit(models.TextChoices):
    """Measurement units."""
    MM = 'mm', 'Millimeters'
    INCH = 'in', 'Inches'
    UM = 'um', 'Micrometers'


# =============================================================================
# FEATURE MODEL
# =============================================================================

class Feature(models.Model):
    """
    A measurable feature with dynamic inputs and formula configuration.
    
    Inputs are defined via related FeatureInput records (A, B, C, ...).
    The formula is a string expression like "A + B" or "(A - B) / 2".
    """
    
    # === Identification ===
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    feature_type = models.CharField(
        max_length=3,
        choices=FeatureType.choices,
        default=FeatureType.DEVIATION
    )
    part_name = models.CharField(max_length=100, blank=True)
    part_number = models.CharField(max_length=100, blank=True)
    
    # === Formula ===
    # Expression using input labels: "A", "A + B", "(A - B) / 2", "abs(A - B)", etc.
    formula = models.CharField(
        max_length=200,
        default='A',
        help_text="Expression using inputs A, B, C... e.g., 'A + B' or '(A - B) / 2'"
    )
    
    # === Tolerance Configuration ===
    tolerance_mode = models.CharField(
        max_length=5,
        choices=ToleranceMode.choices,
        default=ToleranceMode.BILATERAL
    )
    nominal = models.FloatField(
        null=True,
        blank=True,
        help_text="Nominal/target value (not used for LIMIT mode)"
    )
    tolerance_upper = models.FloatField(
        null=True,
        blank=True,
        help_text="Upper tolerance limit (or single limit for LIMIT mode)"
    )
    tolerance_lower = models.FloatField(
        null=True,
        blank=True,
        help_text="Lower tolerance limit (not used for LIMIT or UNILATERAL_POS mode)"
    )
    
    # === Warning Limits (optional, for yellow zone) ===
    warning_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Warning triggers at this percent of tolerance (0-100)"
    )
    
    # === Display Settings ===
    unit = models.CharField(
        max_length=2,
        choices=Unit.choices,
        default=Unit.MM
    )
    resolution = models.IntegerField(
        default=4,
        help_text="Decimal places for display"
    )
    
    # === Metadata ===
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_feature_type_display()})"
    
    # =========================================================================
    # INPUT HELPERS
    # =========================================================================
    
    def get_inputs_ordered(self):
        """Get inputs ordered by label (A, B, C, ...)."""
        return self.inputs.all().order_by('label')
    
    def get_input_labels(self) -> List[str]:
        """Get list of input labels."""
        return list(self.inputs.values_list('label', flat=True).order_by('label'))
    
    def get_next_input_label(self) -> str:
        """Get the next available input label (A, B, C, ... Z, AA, AB, ...)."""
        existing = set(self.get_input_labels())
        
        # Try single letters first
        for i in range(26):
            label = chr(65 + i)  # A-Z
            if label not in existing:
                return label
        
        # Then try double letters
        for i in range(26):
            for j in range(26):
                label = chr(65 + i) + chr(65 + j)  # AA-ZZ
                if label not in existing:
                    return label
        
        return 'A'  # Fallback
    
    @property
    def formula_description(self) -> str:
        """Human-readable formula description."""
        inputs = self.get_inputs_ordered()
        if not inputs.exists():
            return "No inputs configured"
        
        # Build description showing input mappings
        mappings = [f"{inp.label}=CH{inp.channel_index + 1}" for inp in inputs]
        return f"{self.formula} where {', '.join(mappings)}"
    
    # =========================================================================
    # FORMULA EVALUATION
    # =========================================================================
    
    def evaluate_formula(self, channel_values: Dict[int, float]) -> Optional[float]:
        """
        Evaluate the formula with given channel values.
        
        Args:
            channel_values: Dict mapping channel index to value, e.g., {0: 0.012, 1: -0.003}
        
        Returns:
            Computed result, or None if required channels are missing
        """
        # Build variable dict from inputs
        variables = {}
        for inp in self.inputs.all():
            value = channel_values.get(inp.channel_index)
            if value is None:
                return None  # Missing required input
            variables[inp.label] = value
        
        if not variables:
            return None
        
        # Evaluate the formula
        try:
            result = self._safe_eval(self.formula, variables)
            return result
        except Exception:
            return None
    
    def _safe_eval(self, expression: str, variables: Dict[str, float]) -> float:
        """
        Safely evaluate a mathematical expression.
        
        Allowed: +, -, *, /, (), abs(), min(), max(), sqrt(), numbers, input labels
        """
        # Allowed names
        allowed_names = {
            'abs': abs,
            'min': min,
            'max': max,
            'sqrt': math.sqrt,
        }
        allowed_names.update(variables)
        
        # Replace input labels with their values (longest first to avoid partial matches)
        eval_expr = expression.upper()
        for label in sorted(variables.keys(), key=len, reverse=True):
            eval_expr = eval_expr.replace(label, str(variables[label]))
        
        # Evaluate with restricted builtins
        result = eval(eval_expr, {"__builtins__": {}, "abs": abs, "min": min, "max": max, "sqrt": math.sqrt}, {})
        return float(result)
    
    # =========================================================================
    # TOLERANCE EVALUATION
    # =========================================================================
    
    def evaluate_tolerance(self, value: float) -> dict:
        """
        Evaluate a value against tolerance.
        
        Returns:
            Dict with:
                - in_tolerance: bool (None if no tolerance configured)
                - in_warning: bool (within tolerance but in warning zone)
                - deviation: float (from nominal, if applicable)
                - status: 'OK' | 'WARN' | 'ALARM' | 'NONE'
        """
        # If no tolerance configured, just return the value with no status
        if self.tolerance_upper is None:
            return {
                'in_tolerance': None,
                'in_warning': False,
                'deviation': value - (self.nominal or 0),
                'status': 'NONE',
                'value': value
            }
        
        mode = self.tolerance_mode
        warn_pct = self.warning_percent  # May be None
        
        if mode == ToleranceMode.LIMIT:
            # LIMIT mode: value must be between 0 and limit
            in_tolerance = 0 <= value <= self.tolerance_upper
            deviation = value
            
            # Warning check (only if warning_percent is set)
            in_warning = False
            if warn_pct is not None and in_tolerance:
                warning_threshold = self.tolerance_upper * (warn_pct / 100)
                in_warning = value > warning_threshold
        
        elif mode == ToleranceMode.BILATERAL:
            # BILATERAL mode: value must be within nominal ± tolerance
            nominal = self.nominal or 0
            deviation = value - nominal
            
            upper = self.tolerance_upper
            lower = self.tolerance_lower if self.tolerance_lower is not None else -upper
            
            in_tolerance = lower <= deviation <= upper
            
            # Warning check (only if warning_percent is set)
            in_warning = False
            if warn_pct is not None and in_tolerance:
                warn_upper = upper * (warn_pct / 100)
                warn_lower = lower * (warn_pct / 100)
                in_warning = deviation > warn_upper or deviation < warn_lower
        
        elif mode == ToleranceMode.UNILATERAL_POS:
            # UNILATERAL_POS: value must be between nominal and nominal + upper
            nominal = self.nominal or 0
            deviation = value - nominal
            
            in_tolerance = 0 <= deviation <= self.tolerance_upper
            
            in_warning = False
            if warn_pct is not None and in_tolerance:
                warn_threshold = self.tolerance_upper * (warn_pct / 100)
                in_warning = deviation > warn_threshold
        
        elif mode == ToleranceMode.UNILATERAL_NEG:
            # UNILATERAL_NEG: value must be between nominal - lower and nominal
            nominal = self.nominal or 0
            deviation = value - nominal
            lower = self.tolerance_lower if self.tolerance_lower is not None else -self.tolerance_upper
            
            in_tolerance = lower <= deviation <= 0
            
            in_warning = False
            if warn_pct is not None and in_tolerance:
                warn_threshold = lower * (warn_pct / 100)
                in_warning = deviation < warn_threshold
        
        else:
            # Default fallback
            in_tolerance = True
            in_warning = False
            deviation = value - (self.nominal or 0)
        
        # Determine status
        if not in_tolerance:
            status = 'ALARM'
        elif in_warning:
            status = 'WARN'
        else:
            status = 'OK'
        
        return {
            'in_tolerance': in_tolerance,
            'in_warning': in_warning,
            'deviation': deviation,
            'status': status,
            'value': value
        }
    
    def evaluate(self, channel_values: Dict[int, float]) -> Optional[dict]:
        """
        Full evaluation: apply formula, then check tolerance.
        
        Args:
            channel_values: Dict mapping channel index to value
        
        Returns:
            Evaluation result dict, or None if formula fails
        """
        value = self.evaluate_formula(channel_values)
        if value is None:
            return None
        
        result = self.evaluate_tolerance(value)
        result['feature_id'] = self.id
        result['feature_name'] = self.name
        return result


# =============================================================================
# FEATURE INPUT MODEL
# =============================================================================

class FeatureInput(models.Model):
    """
    A single input channel for a Feature.
    
    Each input has a label (A, B, C, ...) and maps to a hardware channel.
    """
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='inputs'
    )
    label = models.CharField(
        max_length=2,
        help_text="Input label (A, B, C, ... Z, AA, AB, ...)"
    )
    channel_index = models.PositiveIntegerField(
        help_text="Hardware channel index (0-based)"
    )
    
    class Meta:
        verbose_name = "Feature Input"
        verbose_name_plural = "Feature Inputs"
        unique_together = ['feature', 'label']
        ordering = ['feature', 'label']
    
    def __str__(self):
        return f"{self.feature.name} Input {self.label} → CH{self.channel_index + 1}"
    
    @property
    def display_channel(self) -> str:
        """Display-friendly channel number (1-indexed)."""
        return f"CH{self.channel_index + 1}"


# =============================================================================
# MEASUREMENT MODEL
# =============================================================================

class Measurement(models.Model):
    """A single measurement result."""
    
    feature = models.ForeignKey(
        Feature, 
        on_delete=models.CASCADE, 
        related_name='measurements'
    )
    
    # Raw channel values stored as JSON for flexibility with dynamic inputs
    channel_values = models.JSONField(
        default=dict,
        help_text="Dict of channel_index: value"
    )
    
    # Computed result
    computed_value = models.FloatField(
        help_text="Result after formula evaluation"
    )
    deviation = models.FloatField(
        help_text="Deviation from nominal (or value itself for LIMIT mode)"
    )
    
    # Tolerance result
    in_tolerance = models.BooleanField()
    in_warning = models.BooleanField(default=False)
    status = models.CharField(max_length=5)  # OK, WARN, ALARM
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    source = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Source identifier (e.g., 'N1700')"
    )
    
    class Meta:
        verbose_name = "Measurement"
        verbose_name_plural = "Measurements"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['feature', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.feature.name}: {self.computed_value:.4f} [{self.status}] @ {self.timestamp}"
    
    @classmethod
    def create_from_channels(
        cls,
        feature: Feature,
        channel_values: Dict[int, float],
        source: str = ''
    ) -> Optional['Measurement']:
        """
        Create a measurement from raw channel values.
        
        Evaluates the feature's formula and tolerance automatically.
        """
        result = feature.evaluate(channel_values)
        if result is None:
            return None
        
        return cls.objects.create(
            feature=feature,
            channel_values=channel_values,
            computed_value=result['value'],
            deviation=result['deviation'],
            in_tolerance=result['in_tolerance'],
            in_warning=result['in_warning'],
            status=result['status'],
            source=source
        )


# =============================================================================
# OFFSET MODEL
# =============================================================================

class Offset(models.Model):
    """Tool offset sent to controller."""
    
    measurement = models.ForeignKey(
        Measurement,
        on_delete=models.CASCADE,
        related_name='offsets'
    )
    controller = models.CharField(max_length=100)
    tool_number = models.IntegerField()
    offset_value = models.FloatField()
    applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Offset"
        verbose_name_plural = "Offsets"
        ordering = ['-applied_at']
    
    def __str__(self):
        status = "✓" if self.applied else "✗"
        return f"T{self.tool_number}: {self.offset_value:+.6f} [{status}]"