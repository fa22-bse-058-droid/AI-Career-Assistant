"""
Views for Jobs app.
"""
from django.db.models import Q, Subquery, OuterRef, FloatField
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobListing, UserJobMatch, SavedJob, ScraperRun
from .serializers import (
    JobListingSerializer,
    JobListingDetailSerializer,
    UserJobMatchSerializer,
    JobApplicationSerializer,
    ScraperRunSerializer,
)


class JobsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class JobListView(generics.ListAPIView):
    """GET /api/jobs/ — filtered, paginated, annotated with match score."""

    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = JobsPagination

    def get_queryset(self):
        qs = JobListing.objects.filter(is_active=True)
        params = self.request.query_params

        # --- filters ---
        source = params.get("source")
        if source:
            qs = qs.filter(source=source)

        job_type = params.get("job_type")
        if job_type:
            qs = qs.filter(job_type=job_type)

        experience_level = params.get("experience_level")
        if experience_level:
            qs = qs.filter(experience_level=experience_level)

        location = params.get("location")
        if location:
            qs = qs.filter(location__icontains=location)

        search = params.get("search")
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(company__icontains=search))

        skills = params.get("skills")
        if skills:
            for skill in skills.split(","):
                skill = skill.strip()
                if skill:
                    qs = qs.filter(skills_required__icontains=skill)

        saved = params.get("saved")
        if saved and saved.lower() == "true":
            saved_ids = SavedJob.objects.filter(
                user=self.request.user
            ).values_list("job_id", flat=True)
            qs = qs.filter(id__in=saved_ids)

        # --- annotate match score ---
        qs = qs.annotate(
            _match_score=Subquery(
                UserJobMatch.objects.filter(
                    user=self.request.user,
                    job=OuterRef("pk"),
                ).values("score")[:1],
                output_field=FloatField(),
            )
        )

        # --- min_score filter ---
        min_score = params.get("min_score")
        if min_score:
            try:
                qs = qs.filter(_match_score__gte=float(min_score))
            except ValueError:
                pass

        # --- ordering: match score DESC (NULLs last), then scraped_at DESC ---
        from django.db.models import F
        qs = qs.order_by(
            F("_match_score").desc(nulls_last=True),
            "-scraped_at",
        )
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        objects = page if page is not None else qs

        # Build match_scores dict for serializer context
        job_ids = [str(j.id) for j in objects]
        match_scores = dict(
            UserJobMatch.objects.filter(
                user=request.user, job_id__in=job_ids
            ).values_list("job_id", "score")
        )
        match_scores = {str(k): v for k, v in match_scores.items()}

        # Build saved_ids set for serializer context
        saved_ids = set(
            str(jid) for jid in SavedJob.objects.filter(
                user=request.user, job_id__in=job_ids
            ).values_list("job_id", flat=True)
        )

        serializer = self.get_serializer(
            objects,
            many=True,
            context={
                **self.get_serializer_context(),
                "match_scores": match_scores,
                "saved_ids": saved_ids,
            },
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class JobDetailView(generics.RetrieveAPIView):
    """GET /api/jobs/{id}/"""

    queryset = JobListing.objects.all()
    serializer_class = JobListingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        match = UserJobMatch.objects.filter(user=request.user, job=instance).first()
        match_scores = {str(instance.id): match.score} if match else {}
        serializer = self.get_serializer(
            instance,
            context={
                **self.get_serializer_context(),
                "match_scores": match_scores,
            },
        )
        return Response(serializer.data)


class UserMatchesView(generics.ListAPIView):
    """GET /api/jobs/matches/ — user's matches with score >= 0.50."""

    serializer_class = UserJobMatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = JobsPagination

    def get_queryset(self):
        return (
            UserJobMatch.objects.filter(user=self.request.user, score__gte=0.50)
            .select_related("job")
            .order_by("-score")
        )


class SaveJobView(APIView):
    """POST/DELETE /api/jobs/{id}/save/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            job = JobListing.objects.get(pk=pk)
        except JobListing.DoesNotExist:
            return Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        SavedJob.objects.get_or_create(user=request.user, job=job)
        return Response({"saved": True}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        deleted, _ = SavedJob.objects.filter(user=request.user, job_id=pk).delete()
        return Response({"saved": False}, status=status.HTTP_200_OK)


class TriggerScrapeView(APIView):
    """POST /api/jobs/scrape/trigger/ — admin only."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        from .tasks import scrape_all_sources
        result = scrape_all_sources.delay()
        return Response(
            {"task_id": str(result.id), "message": "Scrape triggered for all sources."},
            status=status.HTTP_202_ACCEPTED,
        )


class ScraperStatusView(generics.ListAPIView):
    """GET /api/jobs/scrape/status/ — last 10 ScraperRun records."""

    serializer_class = ScraperRunSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return ScraperRun.objects.all()[:10]


class TriggerMatchComputeView(APIView):
    """POST /api/jobs/matches/compute/ — queue match computation for current user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .tasks import compute_matches_for_user
        result = compute_matches_for_user.delay(str(request.user.id))
        return Response(
            {"task_id": str(result.id), "message": "Match computation started."},
            status=status.HTTP_202_ACCEPTED,
        )
