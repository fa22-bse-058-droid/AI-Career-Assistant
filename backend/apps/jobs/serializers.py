"""
Serializers for Jobs app.
"""
from rest_framework import serializers
from .models import JobListing, JobMatch


class JobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobListing
        fields = [
            "id", "title", "company", "location", "description", "requirements",
            "salary_min", "salary_max", "job_type", "experience_level",
            "skills_required", "source", "url", "is_active",
            "scraped_at", "posted_at", "expires_at",
        ]


class JobMatchSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)

    class Meta:
        model = JobMatch
        fields = ["id", "job", "match_score", "semantic_score", "keyword_score",
                  "is_bookmarked", "computed_at"]
