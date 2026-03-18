"""
Serializers for Jobs app.
"""
from rest_framework import serializers
from .models import JobListing, UserJobMatch, JobApplication, ScraperRun, SavedJob


class JobListingSerializer(serializers.ModelSerializer):
    """Minimal serializer used in list views."""

    days_remaining = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    skills_required = serializers.SerializerMethodField()

    class Meta:
        model = JobListing
        fields = [
            "id", "title", "company", "location", "job_type", "experience_level",
            "salary_display", "source", "scraped_at", "days_remaining",
            "is_active", "skills_required", "match_score", "is_saved",
        ]

    def get_days_remaining(self, obj) -> int:
        return obj.days_remaining()

    def get_match_score(self, obj) -> float | None:
        scores = self.context.get("match_scores")
        if scores:
            return scores.get(str(obj.id))
        return None

    def get_is_saved(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        saved_ids = self.context.get("saved_ids")
        if saved_ids is not None:
            return str(obj.id) in saved_ids
        return SavedJob.objects.filter(user=request.user, job=obj).exists()

    def get_skills_required(self, obj) -> list:
        skills = obj.skills_required or []
        return skills[:5]


class JobListingDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""

    days_remaining = serializers.SerializerMethodField()
    formatted_salary = serializers.CharField(source="formatted_salary", read_only=True)
    application_count = serializers.SerializerMethodField()
    user_application_status = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = JobListing
        fields = [
            "id", "title", "company", "location", "job_type", "experience_level",
            "description", "requirements", "salary_min", "salary_max",
            "salary_display", "formatted_salary", "url", "source", "scraped_at",
            "expires_at", "days_remaining", "is_active", "skills_required",
            "application_count", "user_application_status", "match_score", "is_saved",
        ]

    def get_days_remaining(self, obj) -> int:
        return obj.days_remaining()

    def get_application_count(self, obj) -> int:
        return obj.applications.count()

    def get_user_application_status(self, obj) -> str | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        app = obj.applications.filter(user=request.user).first()
        return app.status if app else None

    def get_match_score(self, obj) -> float | None:
        scores = self.context.get("match_scores")
        if scores:
            return scores.get(str(obj.id))
        return None

    def get_is_saved(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return SavedJob.objects.filter(user=request.user, job=obj).exists()


class UserJobMatchSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)
    score_percentage = serializers.IntegerField(source="score_percentage", read_only=True)
    match_label = serializers.CharField(source="match_label", read_only=True)

    class Meta:
        model = UserJobMatch
        fields = [
            "id", "job", "score", "score_percentage", "match_label",
            "skill_overlap", "skill_overlap_count", "computed_at",
        ]


class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = ["id", "job", "status", "applied_at", "auto_applied"]


class ScraperRunSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.FloatField(source="duration_seconds", read_only=True)

    class Meta:
        model = ScraperRun
        fields = [
            "id", "source", "triggered_by", "started_at", "ended_at",
            "jobs_found", "jobs_added", "jobs_updated", "jobs_skipped",
            "errors", "status", "duration_seconds",
        ]


# ---------------------------------------------------------------------------
# Legacy serializer kept for auto_apply app compatibility
# ---------------------------------------------------------------------------

class JobMatchSerializer(serializers.Serializer):
    """Minimal serializer shim; delegates to UserJobMatch."""

    id = serializers.UUIDField(read_only=True)
    job = JobListingSerializer(read_only=True)
    score = serializers.FloatField(read_only=True)
    computed_at = serializers.DateTimeField(read_only=True)
