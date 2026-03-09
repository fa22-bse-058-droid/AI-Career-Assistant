"""
Resource Hub views.
"""
from django.core.cache import cache
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Resource
from .serializers import ResourceSerializer


class ResourceListView(generics.ListAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Resource.objects.all()
        platform = self.request.query_params.get("platform")
        difficulty = self.request.query_params.get("difficulty")
        free_only = self.request.query_params.get("free_only")
        if platform:
            qs = qs.filter(platform=platform)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if free_only == "true":
            qs = qs.filter(is_free=True)
        return qs


class RecommendedResourcesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cache_key = f"resource_recommendations_{request.user.id}"
        data = cache.get(cache_key)
        if data:
            return Response(data)

        # Get skill gaps from latest CV analysis
        from apps.cv_analyzer.models import CVUpload, CVAnalysis
        try:
            latest_cv = (
                CVUpload.objects.filter(user=request.user, status="completed")
                .order_by("-uploaded_at")
                .first()
            )
            if not latest_cv:
                return Response([])

            skill_gaps = latest_cv.analysis.skill_gaps
            if not skill_gaps:
                return Response([])

            # Collect all missing skills
            missing_skills = set()
            for role_gaps in skill_gaps.values():
                missing_skills.update(role_gaps.get("missing_required", []))
                missing_skills.update(role_gaps.get("missing_preferred", []))

            if not missing_skills:
                return Response([])

            # Find resources matching missing skills
            recommendations = {}
            for skill in list(missing_skills)[:10]:
                resources = Resource.objects.filter(
                    skill_tags__contains=[skill]
                ).order_by("is_free", "-rating")[:5]
                if resources.exists():
                    recommendations[skill] = ResourceSerializer(resources, many=True).data

            data = recommendations
            cache.set(cache_key, data, timeout=3600)
            return Response(data)

        except Exception:
            return Response([])
