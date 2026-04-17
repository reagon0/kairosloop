# dashboard/urls.py
from django.urls import path
from .views import dashboard, setup, toggle_feature, toggle_compensation_rule, toggle_controller, toggle_gauge

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('setup/', setup, name='setup'),
    path('setup/toggle/feature/<int:feature_id>/', toggle_feature, name='toggle_feature'),
    path('setup/toggle/rule/<int:rule_id>/', toggle_compensation_rule, name='toggle_rule'),
    path('setup/toggle/controller/<int:controller_id>/', toggle_controller, name='toggle_controller'),
    path('setup/toggle/gauge/<int:gauge_id>/', toggle_gauge, name='toggle_gauge'),
]