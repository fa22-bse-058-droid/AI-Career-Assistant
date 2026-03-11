"""
Admin Panel URL patterns.
"""
from django.urls import path
from .views import (
    AdminUserListView, AdminUserDetailView, AdminStatsView,
    AdminUserExportView, AdminForumPostDeleteView,
    AdminTriggerScraperView, AuditLogListView,
)

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-users"),
    path("users/<uuid:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("users/export/", AdminUserExportView.as_view(), name="admin-user-export"),
    path("forum/posts/<uuid:post_id>/delete/", AdminForumPostDeleteView.as_view(), name="admin-forum-delete"),
    path("scraper/trigger/", AdminTriggerScraperView.as_view(), name="admin-scraper-trigger"),
    path("audit-logs/", AuditLogListView.as_view(), name="admin-audit-logs"),
]
