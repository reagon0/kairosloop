# dmis/admin.py

from django.contrib import admin
from .models import Feature, Tolerance, Measurement, Offset


class ToleranceInline(admin.StackedInline):
    model = Tolerance
    extra = 0


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'feature_type', 'nominal', 'unit', 'part_name', 'active']
    list_filter = ['feature_type', 'unit', 'active', 'part_name']
    search_fields = ['name', 'part_name']
    inlines = [ToleranceInline]


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['feature', 'actual', 'get_deviation', 'get_in_tolerance', 'timestamp', 'source']
    list_filter = ['feature', 'timestamp', 'source']
    search_fields = ['feature__name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']
    
    def get_deviation(self, obj):
        return f"{obj.deviation:+.6f}"
    get_deviation.short_description = "Deviation"
    
    def get_in_tolerance(self, obj):
        return "✓" if obj.in_tolerance else "✗"
    get_in_tolerance.short_description = "OK"


@admin.register(Offset)
class OffsetAdmin(admin.ModelAdmin):
    list_display = ['measurement', 'controller', 'tool_number', 'offset_value', 'applied', 'applied_at']
    list_filter = ['controller', 'tool_number', 'applied']
    date_hierarchy = 'applied_at'