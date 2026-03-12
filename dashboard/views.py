# dashboard/views.py
from django.shortcuts import render

def dashboard(request):
    """Main dashboard view."""
    return render(request, 'dashboard/dashboard.html')