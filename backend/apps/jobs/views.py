"""
Views for Jobs app.
"""
from django.core.cache import cache
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import JobListing, JobApplication, UserJobMatch, SavedJob, ScraperRun
from .serializers import (
    JobListingSerializer,
    JobApplicationSerializer,
    UserJobMatchSerializer,
    SavedJobSerializer,
    ScraperRunSerializer,
)


class JobListView(generics.ListAPIView):
    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["job_type", "experience_level", "source", "is_active", "is_remote"]
    search_fields = ["title", "company", "location", "description"]
    ordering_fields = ["scraped_at", "expires_at"]

    def get_queryset(self):
        qs = JobListing.objects.filter(is_active=True)
        salary_min = self.request.query_params.get("salary_min")
        salary_max = self.request.query_params.get("salary_max")
        if salary_min:
            qs = qs.filter(salary_min__gte=salary_min)
        if salary_max:
            qs = qs.filter(salary_max__lte=salary_max)
        return qs

    def list(self, request, *args, **kwargs):
        cache_key = f"job_listings_{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=120)
        return response


class JobDetailView(generics.RetrieveAPIView):
    queryset = JobListing.objects.all()
    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyMatchesView(generics.ListAPIView):
    serializer_class = UserJobMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            UserJobMatch.objects.filter(user=self.request.user)
            .select_related("job")
            .order_by("-score")
        )


class JobApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            JobApplication.objects.filter(user=self.request.user)
            .select_related("job")
            .order_by("-applied_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class JobApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)


class SavedJobListView(generics.ListAPIView):
    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            SavedJob.objects.filter(user=self.request.user)
            .select_related("job")
            .order_by("-saved_at")
        )


class SaveJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        try:
            job = JobListing.objects.get(pk=job_id)
        except JobListing.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)

        saved_job, created = SavedJob.objects.get_or_create(
            user=request.user, job=job
        )
        if not created:
            saved_job.delete()
            return Response({"saved": False}, status=status.HTTP_200_OK)
        return Response({"saved": True}, status=status.HTTP_201_CREATED)


class ScraperRunListView(generics.ListAPIView):
    serializer_class = ScraperRunSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ScraperRun.objects.all().order_by("-started_at")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["source", "status", "triggered_by"]
