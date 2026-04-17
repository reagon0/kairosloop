# compensation/admin.py
from django.contrib import admin
from .models import CompensationRule, CompensationEvent


@admin.register(CompensationRule)
class CompensationRuleAdmin(admin.ModelAdmin):
    list_display = ['feature', 'tool_assignment', 'trigger_mode', 'active', 'wear_status']
    list_filter = ['active', 'trigger_mode', 'tool_assignment__controller']
    
    @admin.display(description='Wear')
    def wear_status(self, obj):
        pct = obj.wear_percentage
        return f"{pct:.0f}%"


@admin.register(CompensationEvent)
class CompensationEventAdmin(admin.ModelAdmin):
    list_display = ['rule', 'timestamp', 'deviation_in', 'offset_applied', 'status']
    list_filter = ['status', 'rule']
    date_hierarchy = 'timestamp'