"""
Admin Panel views — RBAC-protected.
"""
import csv
import io
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import CustomUser, UserProfile
from apps.authentication.permissions import IsAdmin
from apps.authentication.serializers import UserSerializer
from .models import AuditLog
from .serializers import AuditLogSerializer, AdminUserSerializer, AdminStatsSerializer


def _get_scraper_health() -> dict:
    """Get latest scraper log per source — MySQL compatible."""
    from apps.jobs.models import ScraperLog
    from django.db.models import Max

    # Get latest started_at per source
    latest_per_source = (
        ScraperLog.objects.values("source")
        .annotate(latest=Max("started_at"))
    )
    health = {}
    for row in latest_per_source:
        log = ScraperLog.objects.filter(
            source=row["source"], started_at=row["latest"]
        ).first()
        if log:
            health[log.source] = {
                "last_run": str(log.started_at),
                "status": log.status,
                "jobs_added": log.jobs_added,
            }
    return health


def log_admin_action(admin, action, target_model="", target_id="", details=None, ip=None):
    AuditLog.objects.create(
        admin=admin,
        action=action,
        target_model=target_model,
        target_id=str(target_id),
        details=details or {},
        ip_address=ip,
    )


class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        qs = CustomUser.objects.select_related("profile").order_by("-date_joined")
        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs


class AdminUserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        new_role = request.data.get("role")
        is_active = request.data.get("is_active")

        if new_role and new_role in [r.value for r in CustomUser.Role]:
            user.role = new_role
        if is_active is not None:
            user.is_active = bool(is_active)

        user.save()
        log_admin_action(
            request.user, "update_user", "CustomUser", user.id,
            {"role": new_role, "is_active": is_active},
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(UserSerializer(user).data)


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        cache_key = "admin_stats"
        data = cache.get(cache_key)
        if data:
            return Response(data)

        from apps.cv_analyzer.models import CVUpload
        from apps.jobs.models import JobListing, ScraperLog
        from apps.auto_apply.models import ApplicationLog

        now = timezone.now()
        data = {
            "total_users": CustomUser.objects.count(),
            "active_users": CustomUser.objects.filter(is_active=True).count(),
            "total_cvs": CVUpload.objects.count(),
            "total_jobs": JobListing.objects.filter(is_active=True).count(),
            "total_applications": ApplicationLog.objects.count(),
            "users_by_role": dict(
                CustomUser.objects.values("role").annotate(count=Count("id")).values_list("role", "count")
            ),
            "scraper_health": _get_scraper_health(),
        }

        cache.set(cache_key, data, timeout=3600)
        return Response(data)


class AdminUserExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        def row_generator():
            yield ["ID", "Email", "Username", "Role", "Active", "Joined"]
            for user in CustomUser.objects.values_list(
                "id", "email", "username", "role", "is_active", "date_joined"
            ):
                yield [str(v) for v in user]

        pseudo_buffer = _Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in row_generator()),
            content_type="text/csv",
        )
        response["Content-Disposition"] = 'attachment; filename="users_export.csv"'
        log_admin_action(request.user, "export_users", ip=request.META.get("REMOTE_ADDR"))
        return response


class _Echo:
    def write(self, value):
        return value


class AdminForumPostDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def delete(self, request, post_id):
        from apps.forum.models import ForumPost
        try:
            post = ForumPost.objects.get(pk=post_id)
            post.is_deleted = True
            post.save(update_fields=["is_deleted"])
            log_admin_action(
                request.user, "delete_forum_post", "ForumPost", post_id,
                ip=request.META.get("REMOTE_ADDR"),
            )
            return Response({"detail": "Post deleted."})
        except ForumPost.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)


class AdminTriggerScraperView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        from apps.jobs.tasks import scrape_all_sources
        scrape_all_sources.delay()
        log_admin_action(
            request.user, "trigger_scraper", ip=request.META.get("REMOTE_ADDR")
        )
        return Response({"detail": "Scrapers triggered."})


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get_queryset(self):
        cutoff = timezone.now() - timedelta(days=365)
        return AuditLog.objects.filter(created_at__gte=cutoff)
