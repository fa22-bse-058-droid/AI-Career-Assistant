"""
Auto-Apply views.
"""
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AutoApplySettings, ApplicationLog
from .serializers import AutoApplySettingsSerializer, ApplicationLogSerializer
from apps.authentication.permissions import IsStudent


class AutoApplySettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = AutoApplySettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_object(self):
        settings_obj, _ = AutoApplySettings.objects.get_or_create(user=self.request.user)
        return settings_obj

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ApplicationLogListView(generics.ListAPIView):
    serializer_class = ApplicationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplicationLog.objects.filter(user=self.request.user).select_related("job")


class TriggerAutoApplyView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request):
        from .tasks import run_auto_apply_for_user
        run_auto_apply_for_user.delay(str(request.user.id))
        return Response({"detail": "Auto-apply task queued."})
