"""
URL patterns for notifications.
"""
from django.urls import path
from .views import NotificationListView, MarkReadView, NotificationPreferenceView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("mark-read/", MarkReadView.as_view(), name="notification-mark-all-read"),
    path("<uuid:pk>/read/", MarkReadView.as_view(), name="notification-mark-read"),
    path("preferences/", NotificationPreferenceView.as_view(), name="notification-preferences"),
]
