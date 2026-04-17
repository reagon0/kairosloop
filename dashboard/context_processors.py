# dashboard/context_processors.py
"""
Context processors for global template data.

Provides machine context to all templates via the nav bar.
"""
from django.core.cache import cache

def machine_context(request):
    """
    Provide active machine context to all templates.
    
    Returns:
        dict with:
            - nav_machine: Machine name or None
            - nav_controller: Controller name or None
    """
    # Cache for 10 seconds to avoid DB hits on every page load
    cache_key = 'nav_machine_context'
    cached = cache.get(cache_key)
    
    if cached is not None:
        return cached
    
    context = {
        'nav_machine': None,
        'nav_controller': None,
    }
    
    try:
        from controller.models import ControllerConfig
        
        # Get active controller (primary one)
        controller = ControllerConfig.objects.filter(
            active=True
        ).select_related('machine').first()
        
        if controller:
            context['nav_controller'] = controller.name
            if controller.machine:
                context['nav_machine'] = controller.machine.name
    except Exception:
        # Fail silently - nav will just show defaults
        pass
    
    cache.set(cache_key, context, 10)
    return context