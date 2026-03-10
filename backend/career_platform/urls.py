from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/cv/", include("apps.cv_analyzer.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/chatbot/", include("apps.chatbot.urls")),
    path("api/resources/", include("apps.resources.urls")),
    path("api/forum/", include("apps.forum.urls")),
    path("api/auto-apply/", include("apps.auto_apply.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/mock-interview/", include("apps.mock_interview.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
