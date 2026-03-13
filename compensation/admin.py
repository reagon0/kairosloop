# compensation/admin.py
from django.contrib import admin
from .models import CompensationRule, CompensationEvent


@admin.register(CompensationRule)
class CompensationRuleAdmin(admin.ModelAdmin):
    list_display = ['feature', 'controller', 'tool_number', 'trigger_mode', 'active', 'accumulated_offset']
    list_filter = ['active', 'trigger_mode', 'controller']


@admin.register(CompensationEvent)
class CompensationEventAdmin(admin.ModelAdmin):
    list_display = ['rule', 'timestamp', 'deviation_in', 'offset_applied', 'status']
    list_filter = ['status', 'rule']
    date_hierarchy = 'timestamp'
