# controller/admin.py
from django.contrib import admin
from .models import ControllerConfig


@admin.register(ControllerConfig)
class ControllerConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'controller_type', 'protocol', 'host', 'port', 'active', 'connected']
    list_filter = ['controller_type', 'protocol', 'active', 'connected']
