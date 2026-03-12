# dashboard/routing.py
"""
WebSocket URL routing for dashboard.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/gauge/$', consumers.GaugeConsumer.as_asgi()),
    re_path(r'ws/gauge/(?P<channel>\d+)/$', consumers.GaugeConsumer.as_asgi()),
]