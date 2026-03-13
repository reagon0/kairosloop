# devices/admin.py

from django.contrib import admin
from .models import Machine, GaugeConfig, ChannelConfig, ControllerConfig, ToolMapping


class GaugeInline(admin.TabularInline):
    model = GaugeConfig
    extra = 0


class ControllerInline(admin.TabularInline):
    model = ControllerConfig
    extra = 0


class ChannelInline(admin.TabularInline):
    model = ChannelConfig
    extra = 0


class ToolMappingInline(admin.TabularInline):
    model = ToolMapping
    extra = 0


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active', 'updated_at']
    list_filter = ['is_active']
    inlines = [GaugeInline, ControllerInline]


@admin.register(GaugeConfig)
class GaugeConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'machine', 'filter_level', 'use_64bit', 'active']
    list_filter = ['active', 'use_64bit', 'machine']
    inlines = [ChannelInline]


@admin.register(ControllerConfig)
class ControllerConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'machine', 'controller_type', 'host', 'port', 'active']
    list_filter = ['controller_type', 'active', 'machine']
    inlines = [ToolMappingInline]