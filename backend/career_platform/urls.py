"""
URL configuration for career_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/cv/", include("apps.cv_analyzer.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/chat/", include("apps.chatbot.urls")),
    path("api/resources/", include("apps.resources.urls")),
    path("api/forum/", include("apps.forum.urls")),
    path("api/auto-apply/", include("apps.auto_apply.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/admin-panel/", include("apps.admin_panel.urls")),
    path("api/interview/", include("apps.mock_interview.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
