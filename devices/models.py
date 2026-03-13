# devices/models.py
"""
Device configuration models.

Hierarchy:
    Machine (one KairosLoop instance per machine, future: multi-machine)
      ├── GaugeConfig (N1700 hardware)
      │     └── ChannelConfig (per channel settings)
      └── ControllerConfig (CNC outputs)
            └── ToolMapping (feature → tool offset)
"""

from django.db import models


class Machine(models.Model):
    """
    A machine/cell/station that KairosLoop monitors.
    
    For now, most installations will have one Machine.
    Model exists to future-proof for multi-machine setups.
    """
    name = models.CharField(
        max_length=100,
        help_text="e.g., 'Tsugami Swiss #3', 'Grinding Cell 1'"
    )
    description = models.TextField(blank=True)
    location = models.CharField(
        max_length=100, 
        blank=True,
        help_text="e.g., 'Building A, Line 2'"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Active machine is shown on dashboard"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_active(cls):
        """Get the currently active machine."""
        return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_or_create_default(cls):
        """Get or create a default machine for single-machine setups."""
        machine = cls.objects.first()
        if not machine:
            machine = cls.objects.create(
                name="Default Machine",
                description="Auto-created default machine"
            )
        return machine


class GaugeConfig(models.Model):
    """Configuration for a gauge/driver setup."""
    
    DRIVER_TYPES = [
        ('n1700', 'Mahr Millimar N1700'),
    ]
    
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='gauges',
        null=True,
        blank=True,
        help_text="Machine this gauge belongs to"
    )
    
    driver_type = models.CharField(
        max_length=20,
        choices=DRIVER_TYPES,
        default='n1700',
        help_text="Gauge driver/hardware type"
    )
    name = models.CharField(max_length=100, unique=True)
    dll_path = models.CharField(max_length=500, blank=True)
    use_64bit = models.BooleanField(default=True)
    
    filter_level = models.IntegerField(
        default=5,
        choices=[
            (0, 'Off (Raw)'),
            (1, '2 samples'),
            (2, '4 samples'),
            (3, '8 samples'),
            (4, '16 samples'),
            (5, '32 samples'),
            (6, '64 samples'),
        ],
        help_text="Digital averaging filter level"
    )
    
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Gauge Configuration"
        verbose_name_plural = "Gauge Configurations"
    
    def __str__(self):
        return f"{self.name}"


class ChannelConfig(models.Model):
    """Configuration for a gauge channel."""
    
    gauge = models.ForeignKey(
        GaugeConfig, 
        on_delete=models.CASCADE, 
        related_name='channels'
    )
    channel_index = models.PositiveIntegerField(
        help_text="0-based channel index (matches hardware)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Friendly name, e.g., 'OD Probe Left'"
    )
    enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['gauge', 'channel_index']
        ordering = ['gauge', 'channel_index']
        verbose_name = "Channel Configuration"
        verbose_name_plural = "Channel Configurations"
    
    def __str__(self):
        return f"CH{self.channel_index + 1}: {self.name}"
    
    def clean(self):
        """Validate channel index is within reasonable bounds."""
        from django.core.exceptions import ValidationError
        if self.channel_index is not None and self.channel_index > 255:
            raise ValidationError({
                'channel_index': 'Channel index cannot exceed 255.'
            })
    
    @property
    def display_index(self):
        """1-based index for display (CH1, CH2, etc.)"""
        return self.channel_index + 1


class ControllerConfig(models.Model):
    """Configuration for a CNC controller."""
    
    CONTROLLER_TYPES = [
        ('test', 'Test Controller'),
        ('fanuc', 'Fanuc (FOCAS)'),
        ('siemens', 'Siemens'),
        ('haas', 'Haas'),
        ('mazak', 'Mazak'),
        ('other', 'Other'),
    ]
    
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='controllers',
        null=True,
        blank=True,
        help_text="Machine this controller belongs to"
    )
    
    name = models.CharField(max_length=100, unique=True)
    controller_type = models.CharField(max_length=20, choices=CONTROLLER_TYPES)
    
    # Connection settings
    host = models.CharField(
        max_length=100, 
        blank=True,
        help_text="IP address for network controllers (e.g., 192.168.1.100)"
    )
    port = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Port number or serial port (e.g., 8193 or COM3)"
    )
    
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Controller Configuration"
        verbose_name_plural = "Controller Configurations"
    
    def __str__(self):
        return f"{self.name} ({self.get_controller_type_display()})"


class ToolMapping(models.Model):
    """Maps features to tool numbers for offset compensation."""
    
    controller = models.ForeignKey(
        ControllerConfig, 
        on_delete=models.CASCADE, 
        related_name='tool_mappings'
    )
    feature = models.ForeignKey(
        'dmis.Feature', 
        on_delete=models.CASCADE, 
        related_name='tool_mappings'
    )
    tool_number = models.IntegerField(
        help_text="Tool number in CNC (e.g., 1 for T01)"
    )
    offset_register = models.CharField(
        max_length=20,
        blank=True,
        help_text="Offset register if different from tool (e.g., 'D01', 'H01')"
    )
    offset_multiplier = models.FloatField(
        default=-1.0, 
        help_text="Multiplier for deviation. -1 = compensate (most common)"
    )
    enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['controller', 'feature']
        verbose_name = "Tool Mapping"
        verbose_name_plural = "Tool Mappings"
    
    def __str__(self):
        return f"{self.controller.name} T{self.tool_number} ← {self.feature.name}"
    
    def calculate_offset(self, deviation: float) -> float:
        """Calculate offset value from deviation."""
        return deviation * self.offset_multiplier