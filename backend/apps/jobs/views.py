"""
Views for Jobs app.
"""
from django.core.cache import cache
from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import JobListing, JobMatch
from .serializers import JobListingSerializer, JobMatchSerializer


class JobListView(generics.ListAPIView):
    serializer_class = JobListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["job_type", "experience_level", "source", "is_active"]
    search_fields = ["title", "company", "location", "description"]
    ordering_fields = ["scraped_at", "posted_at"]

    def get_queryset(self):
        qs = JobListing.objects.filter(is_active=True)
        # Optional salary filter
        salary_min = self.request.query_params.get("salary_min")
        salary_max = self.request.query_params.get("salary_max")
        if salary_min:
            qs = qs.filter(salary_min__gte=salary_min)
        if salary_max:
            qs = qs.filter(salary_max__lte=salary_max)
        return qs

    def list(self, request, *args, **kwargs):
        # Cache job listings for 2 minutes
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
    serializer_class = JobMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            JobMatch.objects.filter(user=self.request.user)
            .select_related("job")
            .order_by("-match_score")
        )


class BookmarkJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        try:
            match = JobMatch.objects.get(user=request.user, job_id=job_id)
            match.is_bookmarked = not match.is_bookmarked
            match.save(update_fields=["is_bookmarked"])
            return Response({"is_bookmarked": match.is_bookmarked})
        except JobMatch.DoesNotExist:
            return Response({"detail": "No match found."}, status=404)
