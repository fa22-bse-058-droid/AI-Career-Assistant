"""
CV Analyzer models.
"""
import uuid
from django.db import models
from django.conf import settings


class CVUpload(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cv_uploads",
    )
    file = models.FileField(upload_to="cvs/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    task_id = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"CV by {self.user.email} [{self.status}]"


class CVAnalysis(models.Model):
    class Grade(models.TextChoices):
        POOR = "poor", "Poor (0-40)"
        AVERAGE = "average", "Average (41-60)"
        GOOD = "good", "Good (61-80)"
        EXCELLENT = "excellent", "Excellent (81-100)"

    cv = models.OneToOneField(CVUpload, on_delete=models.CASCADE, related_name="analysis")
    overall_score = models.FloatField(default=0.0)
    grade = models.CharField(max_length=20, choices=Grade.choices, default=Grade.POOR)
    keyword_relevance_score = models.FloatField(default=0.0)
    completeness_score = models.FloatField(default=0.0)
    skill_density_score = models.FloatField(default=0.0)
    formatting_score = models.FloatField(default=0.0)
    extracted_skills = models.JSONField(default=list)
    skills_by_category = models.JSONField(default=dict)
    skill_gaps = models.JSONField(default=dict)
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    contact_info = models.JSONField(default=dict)
    raw_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.cv} — Score: {self.overall_score:.1f}"

    @staticmethod
    def compute_grade(score):
        if score <= 40:
            return CVAnalysis.Grade.POOR
        elif score <= 60:
            return CVAnalysis.Grade.AVERAGE
        elif score <= 80:
            return CVAnalysis.Grade.GOOD
        return CVAnalysis.Grade.EXCELLENT
