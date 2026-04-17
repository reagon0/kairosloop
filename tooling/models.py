# tooling/models.py
"""
Tooling management models.

ToolType: Definition of a tool/insert type with specifications.
ToolInstance: A specific physical tool (one insert from a box).
ToolAssignment: Tracks which instance is installed in which position on which machine.
"""

import uuid
from django.db import models
from django.utils import timezone


class AssignmentStatus(models.TextChoices):
    """Status of a tool assignment (session in machine)."""
    ACTIVE = 'ACTIVE', 'Active'
    WARNING = 'WARNING', 'Warning (approaching limit)'
    CHANGE_REQUIRED = 'CHANGE', 'Change Required'
    REPLACED = 'REPLACED', 'Replaced'


class InstanceStatus(models.TextChoices):
    """Status of a tool instance (physical insert)."""
    IN_USE = 'IN_USE', 'In Use'
    NOT_IN_USE = 'NOT_IN_USE', 'Not In Use'


# =============================================================================
# TOOL TYPE (Definition / Template)
# =============================================================================

class ToolType(models.Model):
    """
    A tool/insert type definition.
    
    Represents a class of tool (e.g., "CNMG 120408") with its specifications.
    Features reference ToolType to indicate which tool cuts them.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique identifier for tracking and reporting"
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Tool identifier (e.g., 'CNMG 120408', 'OD Roughing Insert')"
    )
    manufacturer = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tool manufacturer (e.g., 'Sandvik', 'Kennametal')"
    )
    part_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Manufacturer part number"
    )
    tool_kind = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of tool (e.g., 'insert', 'boring_bar', 'drill', 'end_mill')"
    )
    
    # Guardrails / Specifications
    max_offset_distance = models.FloatField(
        default=0.1,
        help_text="Maximum total offset allowed before tool change required (mm)"
    )
    
    # Statistics (updated when instances are retired)
    avg_parts_per_instance = models.FloatField(
        default=0.0,
        help_text="Average parts cut per instance (calculated from retired instances)"
    )
    instance_count = models.IntegerField(
        default=0,
        help_text="Total number of instances used (for calculating average)"
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this tool type"
    )
    active = models.BooleanField(
        default=True,
        help_text="Available for new instances"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tool Type"
        verbose_name_plural = "Tool Types"
        ordering = ['name']
    
    def __str__(self):
        if self.manufacturer:
            return f"{self.name} ({self.manufacturer})"
        return self.name
    
    def update_statistics(self, parts_cut: int):
        """
        Update average statistics when an instance is retired.
        
        Uses incremental average: new_avg = (old_avg * n + new_value) / (n + 1)
        """
        old_total = self.avg_parts_per_instance * self.instance_count
        self.instance_count += 1
        self.avg_parts_per_instance = (old_total + parts_cut) / self.instance_count
        self.save(update_fields=['avg_parts_per_instance', 'instance_count', 'updated_at'])


# =============================================================================
# TOOL INSTANCE (Specific Physical Tool)
# =============================================================================

class ToolInstance(models.Model):
    """
    A specific physical tool/insert.
    
    Represents one insert from a box. Tracks lifetime usage across assignments.
    Once removed from machine, it's marked NOT_IN_USE (spent).
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique identifier for this specific physical tool"
    )
    
    tool_type = models.ForeignKey(
        ToolType,
        on_delete=models.PROTECT,
        related_name='instances',
        help_text="Type of tool this instance is"
    )
    
    # Lifetime usage tracking
    total_parts_cut = models.IntegerField(
        default=0,
        help_text="Total parts cut by this instance (lifetime)"
    )
    total_accumulated_wear = models.FloatField(
        default=0.0,
        help_text="Total offset applied to this instance (lifetime)"
    )
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=InstanceStatus.choices,
        default=InstanceStatus.IN_USE,
        help_text="Current status of this instance"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tool Instance"
        verbose_name_plural = "Tool Instances"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tool_type.name} [{str(self.uuid)[:8]}]"
    
    @property
    def usage_percentage(self) -> float:
        """Percentage of tool type's max offset used."""
        if self.tool_type.max_offset_distance == 0:
            return 0.0
        return (abs(self.total_accumulated_wear) / self.tool_type.max_offset_distance) * 100
    
    def retire(self):
        """
        Mark this instance as no longer in use.
        
        Called when the insert is removed from the machine.
        Updates the ToolType statistics with this instance's data.
        """
        if self.status == InstanceStatus.NOT_IN_USE:
            return  # Already retired
        
        self.status = InstanceStatus.NOT_IN_USE
        self.save(update_fields=['status', 'updated_at'])
        
        # Update ToolType statistics
        self.tool_type.update_statistics(self.total_parts_cut)
    
    def add_wear(self, offset_value: float, parts: int = 1):
        """
        Add wear from an assignment session.
        
        Called when offset is applied or cycle completes.
        """
        self.total_accumulated_wear += abs(offset_value)
        self.total_parts_cut += parts
        self.save(update_fields=['total_accumulated_wear', 'total_parts_cut', 'updated_at'])


# =============================================================================
# TOOL ASSIGNMENT (Current Session in Machine)
# =============================================================================

class ToolAssignment(models.Model):
    """
    Tracks a specific tool instance installation in a machine position.
    
    Each time a tool is changed, the old assignment gets removed_at set,
    the instance is retired, and a new assignment with new instance is created.
    """
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique identifier for this specific installation session"
    )
    
    # What's installed
    tool_instance = models.ForeignKey(
        ToolInstance,
        on_delete=models.PROTECT,
        related_name='assignments',
        help_text="Specific tool instance installed"
    )
    
    # Location
    controller = models.ForeignKey(
        'controller.ControllerConfig',
        on_delete=models.CASCADE,
        related_name='tool_assignments',
        help_text="Machine/controller this tool is installed on"
    )
    tool_position = models.IntegerField(
        help_text="Tool position number (e.g., 1 for T1)"
    )
    
    # Lifecycle tracking
    installed_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this tool was installed"
    )
    removed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tool was removed (null if still active)"
    )
    
    # Session usage tracking (this installation only)
    accumulated_offset = models.FloatField(
        default=0.0,
        help_text="Total offset applied this session"
    )
    cycle_count = models.IntegerField(
        default=0,
        help_text="Number of cycles this session"
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.ACTIVE,
        help_text="Current status of this assignment"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tool Assignment"
        verbose_name_plural = "Tool Assignments"
        ordering = ['-installed_at']
        indexes = [
            models.Index(fields=['controller', 'tool_position', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"T{self.tool_position} @ {self.controller.name}: {self.tool_instance.tool_type.name}"
    
    # Convenience accessors
    @property
    def tool_type(self) -> ToolType:
        """Get the tool type for this assignment."""
        return self.tool_instance.tool_type
    
    @property
    def usage_percentage(self) -> float:
        """Percentage of tool type's max offset used (this session)."""
        max_offset = self.tool_type.max_offset_distance
        if max_offset == 0:
            return 0.0
        return (abs(self.accumulated_offset) / max_offset) * 100
    
    @property
    def is_active(self) -> bool:
        """True if this is the current assignment (not replaced)."""
        return self.status != AssignmentStatus.REPLACED
    
    def apply_offset(self, offset_value: float):
        """
        Apply an offset and update accumulated total.
        
        Called by the gateway after successfully sending offset to PLC.
        Updates both the assignment (session) and instance (lifetime).
        """
        abs_offset = abs(offset_value)
        
        # Update session tracking
        self.accumulated_offset += abs_offset
        self.updated_at = timezone.now()
        self.save(update_fields=['accumulated_offset', 'updated_at'])
        
        # Update instance lifetime tracking
        self.tool_instance.add_wear(abs_offset, parts=0)  # Parts added separately
        
        # Check if status should change
        self._update_status()
    
    def increment_cycle(self):
        """Increment cycle count for session and instance."""
        self.cycle_count += 1
        self.save(update_fields=['cycle_count', 'updated_at'])
        
        # Also increment instance lifetime count
        self.tool_instance.total_parts_cut += 1
        self.tool_instance.save(update_fields=['total_parts_cut', 'updated_at'])
    
    def _update_status(self):
        """Update status based on usage."""
        pct = self.usage_percentage
        
        if pct >= 100:
            new_status = AssignmentStatus.CHANGE_REQUIRED
        elif pct >= 80:
            new_status = AssignmentStatus.WARNING
        else:
            new_status = AssignmentStatus.ACTIVE
        
        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])
    
    def replace(self, new_tool_type: ToolType = None) -> 'ToolAssignment':
        """
        Mark this assignment as replaced and create a new one.
        
        Args:
            new_tool_type: ToolType for the new instance. If None, uses same type.
        
        Returns the new active assignment.
        """
        # Mark current assignment as replaced
        self.status = AssignmentStatus.REPLACED
        self.removed_at = timezone.now()
        self.save(update_fields=['status', 'removed_at', 'updated_at'])
        
        # Retire the old instance
        self.tool_instance.retire()
        
        # Determine tool type for new instance
        tool_type = new_tool_type or self.tool_type
        
        # Create new instance
        new_instance = ToolInstance.objects.create(
            tool_type=tool_type,
            status=InstanceStatus.IN_USE,
        )
        
        # Create new assignment
        new_assignment = ToolAssignment.objects.create(
            tool_instance=new_instance,
            controller=self.controller,
            tool_position=self.tool_position,
            installed_at=timezone.now(),
            accumulated_offset=0.0,
            cycle_count=0,
            status=AssignmentStatus.ACTIVE,
        )
        
        return new_assignment
    
    @classmethod
    def get_active(cls, controller, tool_position: int) -> 'ToolAssignment | None':
        """Get the currently active assignment for a position."""
        return cls.objects.filter(
            controller=controller,
            tool_position=tool_position,
            status__in=[
                AssignmentStatus.ACTIVE,
                AssignmentStatus.WARNING,
                AssignmentStatus.CHANGE_REQUIRED
            ]
        ).first()
    
    @classmethod
    def get_or_create_active(
        cls,
        controller,
        tool_position: int,
        tool_type: ToolType
    ) -> 'ToolAssignment':
        """Get active assignment or create one with a new instance."""
        assignment = cls.get_active(controller, tool_position)
        if assignment:
            return assignment
        
        # Create new instance
        instance = ToolInstance.objects.create(
            tool_type=tool_type,
            status=InstanceStatus.IN_USE,
        )
        
        # Create assignment
        return cls.objects.create(
            tool_instance=instance,
            controller=controller,
            tool_position=tool_position,
            status=AssignmentStatus.ACTIVE,
        )