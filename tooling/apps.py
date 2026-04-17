# tooling/apps.py
from django.apps import AppConfig


class ToolingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tooling'
    verbose_name = 'Tooling Management'
