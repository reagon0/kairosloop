# compensation/apps.py
from django.apps import AppConfig


class CompensationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compensation'
    verbose_name = 'Compensation Management'
    
    def ready(self):
        # Import signal handlers to register them
        from . import signals  # noqa: F401
