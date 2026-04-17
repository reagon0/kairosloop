# controller/admin.py
from django.contrib import admin
from .models import ControllerConfig, Machine


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'location']


@admin.register(ControllerConfig)
class ControllerConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'controller_type', 'protocol', 'host', 'port', 'on_tool_limit', 'active', 'connected']
    list_filter = ['controller_type', 'protocol', 'active', 'connected', 'on_tool_limit']
    search_fields = ['name', 'host']
    
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'machine', 'controller_type'),
        }),
        ('Connection', {
            'fields': ('protocol', 'host', 'port', 'timeout_ms'),
        }),
        ('Inbound Signals (PLC → KairosLoop)', {
            'fields': ('signal_cycle_complete', 'signal_master_request', 'signal_part_present', 'signal_tool_change'),
            'classes': ('collapse',),
        }),
        ('Outbound Signals (KairosLoop → PLC)', {
            'fields': ('signal_ready', 'signal_alarm', 'signal_measuring', 'signal_pass', 'signal_fail'),
            'classes': ('collapse',),
        }),
        ('Offset Settings', {
            'fields': ('offset_method', 'offset_resolution', 'offset_write_delay_ms'),
        }),
        ('Tool Limit Behavior', {
            'fields': ('on_tool_limit',),
            'description': 'What happens when a tool reaches its maximum compensation limit. Offsets are always blocked regardless of this setting.',
        }),
        ('State', {
            'fields': ('active', 'connected', 'last_heartbeat', 'last_error'),
        }),
    )
    
    readonly_fields = ['connected', 'last_heartbeat', 'last_error']