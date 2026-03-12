# dmis/models.py
"""
DMIS-based measurement models.
"""

from django.db import models
from django.utils import timezone


class Feature(models.Model):
    """A measurable feature on a part."""
    
    FEATURE_TYPES = [
        ('CIRCLE', 'Circle'),
        ('CYLINDER', 'Cylinder'),
        ('PLANE', 'Plane'),
        ('LINE', 'Line'),
        ('POINT', 'Point'),
        ('CONE', 'Cone'),
        ('SPHERE', 'Sphere'),
    ]
    
    UNITS = [
        ('mm', 'Millimeters'),
        ('inch', 'Inches'),
    ]
    
    name = models.CharField(max_length=100)
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPES)
    nominal = models.FloatField(help_text="Target value")
    unit = models.CharField(max_length=10, choices=UNITS, default='mm')
    x = models.FloatField(null=True, blank=True)
    y = models.FloatField(null=True, blank=True)
    z = models.FloatField(null=True, blank=True)
    part_name = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feature"
        verbose_name_plural = "Features"
    
    def __str__(self):
        return f"{self.name} ({self.nominal} {self.unit})"


class Tolerance(models.Model):
    """Tolerance limits for a feature."""
    
    feature = models.OneToOneField(Feature, on_delete=models.CASCADE, related_name='tolerance')
    upper = models.FloatField(help_text="Upper deviation limit")
    lower = models.FloatField(help_text="Lower deviation limit")
    
    class Meta:
        verbose_name = "Tolerance"
        verbose_name_plural = "Tolerances"
    
    def __str__(self):
        return f"{self.feature.name}: {self.lower:+.4f} / {self.upper:+.4f}"


class Measurement(models.Model):
    """A single measurement reading."""
    
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='measurements')
    actual = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=100, blank=True, help_text="Gauge/channel that took reading")
    
    class Meta:
        verbose_name = "Measurement"
        verbose_name_plural = "Measurements"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.feature.name}: {self.actual} @ {self.timestamp}"
    
    @property
    def deviation(self) -> float:
        return self.actual - self.feature.nominal
    
    @property
    def in_tolerance(self) -> bool:
        try:
            tol = self.feature.tolerance
            return tol.lower <= self.deviation <= tol.upper
        except Tolerance.DoesNotExist:
            return True  # No tolerance = always OK


class Offset(models.Model):
    """Tool offset sent to controller."""
    
    measurement = models.OneToOneField(Measurement, on_delete=models.CASCADE, related_name='offset')
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