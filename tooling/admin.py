# tooling/admin.py
from django.contrib import admin
from .models import ToolType, ToolInstance, ToolAssignment


@admin.register(ToolType)
class ToolTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'manufacturer', 'tool_kind', 'max_offset_distance', 'avg_parts_per_instance', 'instance_count', 'active']
    list_filter = ['manufacturer', 'tool_kind', 'active']
    search_fields = ['name', 'manufacturer', 'part_number']
    readonly_fields = ['uuid', 'avg_parts_per_instance', 'instance_count', 'created_at', 'updated_at']


@admin.register(ToolInstance)
class ToolInstanceAdmin(admin.ModelAdmin):
    list_display = ['uuid_short', 'tool_type', 'status', 'total_parts_cut', 'total_accumulated_wear', 'usage_percentage_display', 'created_at']
    list_filter = ['status', 'tool_type']
    search_fields = ['tool_type__name', 'uuid']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    def uuid_short(self, obj):
        return str(obj.uuid)[:8]
    uuid_short.short_description = "UUID"
    
    def usage_percentage_display(self, obj):
        return f"{obj.usage_percentage:.1f}%"
    usage_percentage_display.short_description = "Usage %"


@admin.register(ToolAssignment)
class ToolAssignmentAdmin(admin.ModelAdmin):
    list_display = ['tool_position', 'controller', 'tool_type_name', 'status', 'accumulated_offset', 'usage_percentage_display', 'installed_at']
    list_filter = ['status', 'controller']
    search_fields = ['tool_instance__tool_type__name', 'controller__name']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    def tool_type_name(self, obj):
        return obj.tool_instance.tool_type.name
    tool_type_name.short_description = "Tool Type"
    
    def usage_percentage_display(self, obj):
        return f"{obj.usage_percentage:.1f}%"
    usage_percentage_display.short_description = "Usage %"