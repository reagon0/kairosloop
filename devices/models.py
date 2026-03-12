# devices/models.py
"""
Device configuration models.
Stores gauge and controller settings in database.
"""

from django.db import models


class GaugeConfig(models.Model):
    """Configuration for an N1700 gauge setup."""
    
    name = models.CharField(max_length=100, unique=True)
    dll_path = models.CharField(max_length=500, blank=True)
    use_64bit = models.BooleanField(default=True)
    polling_rate_hz = models.FloatField(default=10.0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Gauge Configuration"
        verbose_name_plural = "Gauge Configurations"
    
    def __str__(self):
        return f"{self.name} ({self.polling_rate_hz} Hz)"


class ChannelConfig(models.Model):
    """Configuration for a gauge channel."""
    
    gauge = models.ForeignKey(GaugeConfig, on_delete=models.CASCADE, related_name='channels')
    channel_index = models.IntegerField()
    name = models.CharField(max_length=100)
    feature = models.ForeignKey(
        'dmis.Feature', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='channels'
    )
    enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['gauge', 'channel_index']
        verbose_name = "Channel Configuration"
        verbose_name_plural = "Channel Configurations"
    
    def __str__(self):
        return f"{self.gauge.name} Ch{self.channel_index}: {self.name}"


class ControllerConfig(models.Model):
    """Configuration for a CNC controller."""
    
    CONTROLLER_TYPES = [
        ('test', 'Test Controller'),
        ('fanuc', 'Fanuc'),
        ('siemens', 'Siemens'),
        ('haas', 'Haas'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    controller_type = models.CharField(max_length=20, choices=CONTROLLER_TYPES)
    port = models.CharField(max_length=50, blank=True, help_text="e.g., COM3 or /dev/ttyUSB0")
    baudrate = models.IntegerField(default=9600)
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
    
    controller = models.ForeignKey(ControllerConfig, on_delete=models.CASCADE, related_name='tool_mappings')
    feature = models.ForeignKey('dmis.Feature', on_delete=models.CASCADE, related_name='tool_mappings')
    tool_number = models.IntegerField()
    offset_multiplier = models.FloatField(default=-1.0, help_text="Multiplier for deviation. -1 = compensate")
    enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['controller', 'feature']
        verbose_name = "Tool Mapping"
        verbose_name_plural = "Tool Mappings"
    
    def __str__(self):
        return f"{self.controller.name} → T{self.tool_number} ({self.feature.name})"