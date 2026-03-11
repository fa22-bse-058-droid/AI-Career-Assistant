"""
Auto-Apply URL patterns.
"""
from django.urls import path
from .views import AutoApplySettingsView, ApplicationLogListView, TriggerAutoApplyView

urlpatterns = [
    path("settings/", AutoApplySettingsView.as_view(), name="auto-apply-settings"),
    path("logs/", ApplicationLogListView.as_view(), name="auto-apply-logs"),
    path("trigger/", TriggerAutoApplyView.as_view(), name="auto-apply-trigger"),
]
