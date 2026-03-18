"""
Serializers for Jobs app.
"""
from rest_framework import serializers
from .models import JobListing, JobApplication, UserJobMatch, SavedJob, ScraperRun


class JobListingSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    formatted_salary = serializers.CharField(read_only=True)

    class Meta:
        model = JobListing
        fields = [
            "id", "title", "company", "location", "job_type", "experience_level",
            "description", "requirements", "salary_min", "salary_max",
            "salary_display", "url", "source", "is_active", "is_remote",
            "skills_required", "scraped_at", "expires_at",
            "is_expired", "days_remaining", "formatted_salary",
        ]


class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)
    job_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id", "job", "job_id", "applied_at", "status",
            "auto_applied", "cover_letter", "notes",
        ]
        read_only_fields = ["id", "applied_at", "auto_applied"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class UserJobMatchSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)
    score_percentage = serializers.IntegerField(read_only=True)
    match_label = serializers.CharField(read_only=True)

    class Meta:
        model = UserJobMatch
        fields = [
            "id", "job", "score", "skill_overlap", "skill_overlap_count",
            "computed_at", "score_percentage", "match_label",
        ]


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)
    job_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "job_id", "saved_at"]
        read_only_fields = ["id", "saved_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ScraperRunSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = ScraperRun
        fields = [
            "id", "source", "triggered_by", "started_at", "ended_at",
            "jobs_found", "jobs_added", "jobs_updated", "jobs_skipped",
            "errors", "status", "duration_seconds",
        ]
