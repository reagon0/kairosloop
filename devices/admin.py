# devices/admin.py

from django.contrib import admin
from .models import GaugeConfig, ChannelConfig, ControllerConfig, ToolMapping


class ChannelInline(admin.TabularInline):
    model = ChannelConfig
    extra = 0


class ToolMappingInline(admin.TabularInline):
    model = ToolMapping
    extra = 0


@admin.register(GaugeConfig)
class GaugeConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'polling_rate_hz', 'use_64bit', 'active', 'updated_at']
    list_filter = ['active', 'use_64bit']
    inlines = [ChannelInline]


@admin.register(ControllerConfig)
class ControllerConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'controller_type', 'port', 'baudrate', 'active']
    list_filter = ['controller_type', 'active']
    inlines = [ToolMappingInline]