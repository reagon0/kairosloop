# controller/models.py
"""
Controller layer models.

ControllerConfig: CNC/PLC connection and communication settings.
"""

from django.db import models
from django.utils import timezone


class Protocol(models.TextChoices):
    """Communication protocol."""
    FOCAS2 = 'FOCAS2', 'Fanuc FOCAS2'
    MTCONNECT = 'MTC', 'MTConnect'
    OPCUA = 'OPC', 'OPC-UA'
    MODBUS = 'MOD', 'Modbus TCP'
    TEST = 'TEST', 'Test/Simulator'


class OffsetMethod(models.TextChoices):
    """How offsets are written to the CNC."""
    WEAR = 'WEAR', 'Wear Offset'
    GEOMETRY = 'GEOM', 'Geometry Offset'
    MACRO = 'MACRO', 'Macro Variable'


class ToolLimitAction(models.TextChoices):
    """Action when tool reaches its compensation limit."""
    ALARM = 'ALARM', 'Alarm (stop machine)'
    WARNING = 'WARNING', 'Warning only (keep running)'


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

class ControllerConfig(models.Model):
    """
    CNC/PLC connection and communication settings.
    
    Handles:
    - Connection to CNC (FOCAS2, MTConnect, etc.)
    - PLC signal addresses for cycle complete, master, etc.
    - Offset write settings
    """
    
    CONTROLLER_TYPES = [
        ('fanuc', 'Fanuc'),
        ('siemens', 'Siemens'),
        ('haas', 'Haas'),
        ('mazak', 'Mazak'),
        ('mitsubishi', 'Mitsubishi'),
        ('okuma', 'Okuma'),
        ('brother', 'Brother'),
        ('citizen', 'Citizen'),
        ('tsugami', 'Tsugami'),
        ('star', 'Star'),
        ('other', 'Other'),
        ('test', 'Test/Simulator'),
    ]
    
    # === Identity ===
    # Change this line in ControllerConfig:
    machine = models.ForeignKey(
        'Machine',  # Was 'devices.Machine', now local
        on_delete=models.CASCADE,
        related_name='controllers',
        null=True,
        blank=True,
        help_text="Machine this controller belongs to"
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="e.g., 'Tsugami B0205 Main'"
    )
    controller_type = models.CharField(
        max_length=20,
        choices=CONTROLLER_TYPES,
        help_text="CNC manufacturer/type"
    )
    
    # === Connection ===
    protocol = models.CharField(
        max_length=10,
        choices=Protocol.choices,
        default=Protocol.FOCAS2,
        help_text="Communication protocol"
    )
    host = models.CharField(
        max_length=100,
        blank=True,
        help_text="IP address (e.g., 192.168.1.100)"
    )
    port = models.IntegerField(
        default=8193,
        help_text="Port number (FOCAS default: 8193)"
    )
    timeout_ms = models.IntegerField(
        default=1000,
        help_text="Connection timeout in milliseconds"
    )
    
    # === Signals - INBOUND (PLC → KairosLoop) ===
    signal_cycle_complete = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address for cycle complete (e.g., R100.0)"
    )
    signal_master_request = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address for master/zero request"
    )
    signal_part_present = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address for part-in-fixture sensor"
    )
    signal_tool_change = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address for tool change notification"
    )
    
    # === Signals - OUTBOUND (KairosLoop → PLC) ===
    signal_ready = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address to signal measurement complete"
    )
    signal_alarm = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address to signal alarm/fault"
    )
    signal_measuring = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address to signal measurement in progress"
    )
    signal_pass = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address to signal part passed"
    )
    signal_fail = models.CharField(
        max_length=50,
        blank=True,
        help_text="PLC address to signal part failed"
    )
    
    # === Offset Settings ===
    offset_method = models.CharField(
        max_length=5,
        choices=OffsetMethod.choices,
        default=OffsetMethod.WEAR,
        help_text="How offsets are written to CNC"
    )
    offset_resolution = models.FloatField(
        default=0.001,
        help_text="Minimum offset increment CNC accepts (mm)"
    )
    offset_write_delay_ms = models.IntegerField(
        default=50,
        help_text="Delay after writing offset before next operation"
    )
    
    # === Tool Limit Behavior ===
    on_tool_limit = models.CharField(
        max_length=10,
        choices=ToolLimitAction.choices,
        default=ToolLimitAction.ALARM,
        help_text="Action when tool reaches compensation limit (offsets are always blocked)"
    )
    
    # === State ===
    active = models.BooleanField(
        default=True,
        help_text="Enable/disable this controller"
    )
    connected = models.BooleanField(
        default=False,
        help_text="Current connection status (runtime)"
    )
    last_heartbeat = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful communication"
    )
    last_error = models.CharField(
        max_length=200,
        blank=True,
        help_text="Last error message"
    )
    
    # === Metadata ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Controller Configuration"
        verbose_name_plural = "Controller Configurations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_controller_type_display()})"
    
    @property
    def connection_string(self) -> str:
        """Display-friendly connection info."""
        if self.host:
            return f"{self.host}:{self.port}"
        return "Not configured"
    
    @property
    def status_display(self) -> str:
        """Connection status for display."""
        if not self.active:
            return 'disabled'
        if self.connected:
            return 'connected'
        if self.last_error:
            return 'error'
        return 'disconnected'
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.connected = True
        self.last_heartbeat = timezone.now()
        self.last_error = ''
        self.save(update_fields=['connected', 'last_heartbeat', 'last_error', 'updated_at'])
    
    def set_error(self, message: str):
        """Record connection error."""
        self.connected = False
        self.last_error = message[:200]
        self.save(update_fields=['connected', 'last_error', 'updated_at'])