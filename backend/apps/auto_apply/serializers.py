"""
Auto-Apply serializers.
"""
from rest_framework import serializers
from .models import AutoApplySettings, ApplicationLog
from apps.jobs.serializers import JobListingSerializer


class AutoApplySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoApplySettings
        fields = ["is_enabled", "min_match_score", "max_applications_per_day", "target_roles"]


class ApplicationLogSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)

    class Meta:
        model = ApplicationLog
        fields = ["id", "job", "applied_at", "method", "status", "error_message"]
        read_only_fields = fields
