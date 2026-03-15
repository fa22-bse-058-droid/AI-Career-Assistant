"""
Serializers for CV Analyzer.
"""
from rest_framework import serializers
from .models import CVUpload, CVAnalysis, JobCategory


class CVAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVAnalysis
        fields = [
            "id", "overall_score", "grade",
            "keyword_relevance_score", "completeness_score",
            "skill_density_score", "formatting_score",
            "extracted_skills", "skills_by_category", "skill_gaps",
            "education", "experience", "contact_info",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class CVUploadSerializer(serializers.ModelSerializer):
    analysis = CVAnalysisSerializer(read_only=True)

    class Meta:
        model = CVUpload
        fields = [
            "id", "original_filename", "status", "task_id",
            "uploaded_at", "processed_at", "error_message", "analysis",
        ]
        read_only_fields = fields


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ["id", "name", "slug", "required_skills", "description"]
        read_only_fields = fields
