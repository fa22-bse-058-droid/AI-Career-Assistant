"""
Views for CV Analyzer app.
"""
import uuid
import logging
from django.core.cache import cache
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import CVUpload, CVAnalysis
from .serializers import CVUploadSerializer, CVAnalysisSerializer
from .tasks import analyze_cv_task
from apps.authentication.permissions import IsStudent

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@method_decorator(ratelimit(key="user", rate="10/h", method="POST", block=True), name="post")
class CVUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > MAX_FILE_SIZE:
            return Response(
                {"detail": "File too large. Maximum size is 5 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
        if ext not in ALLOWED_EXTENSIONS:
            return Response(
                {"detail": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate UUID filename
        safe_filename = f"{uuid.uuid4()}.{ext}"
        file.name = safe_filename

        cv = CVUpload.objects.create(
            user=request.user,
            file=file,
            original_filename=file.name,
        )

        # Dispatch Celery task
        task = analyze_cv_task.delay(str(cv.id))
        cv.task_id = task.id
        cv.save(update_fields=["task_id"])

        # Invalidate cached CV results for this user
        cache.delete(f"cv_results_{request.user.id}")

        return Response(CVUploadSerializer(cv).data, status=status.HTTP_202_ACCEPTED)


class CVStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cv_id):
        try:
            cv = CVUpload.objects.get(pk=cv_id, user=request.user)
        except CVUpload.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        data = CVUploadSerializer(cv).data
        if cv.status == CVUpload.Status.COMPLETED:
            try:
                cache_key = f"cv_results_{request.user.id}"
                analysis = cache.get(cache_key)
                if analysis is None:
                    analysis = CVAnalysisSerializer(cv.analysis).data
                    cache.set(cache_key, analysis, timeout=86400)  # 24 hours
                data["analysis"] = analysis
            except CVAnalysis.DoesNotExist:
                pass

        return Response(data)


class CVListView(ListAPIView):
    serializer_class = CVUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CVUpload.objects.filter(user=self.request.user).order_by("-uploaded_at")


class CVAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cv_id):
        try:
            cv = CVUpload.objects.get(pk=cv_id, user=request.user)
            analysis = cv.analysis
        except (CVUpload.DoesNotExist, CVAnalysis.DoesNotExist):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(CVAnalysisSerializer(analysis).data)
