"""
Auto-Apply models.
"""
import uuid
from django.db import models
from django.conf import settings


class AutoApplySettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auto_apply_settings",
    )
    is_enabled = models.BooleanField(default=False)
    min_match_score = models.FloatField(default=0.60)
    max_applications_per_day = models.IntegerField(default=5)
    target_roles = models.JSONField(default=list)

    def __str__(self):
        return f"AutoApply for {self.user.email} [{'ON' if self.is_enabled else 'OFF'}]"


class ApplicationLog(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped (Duplicate)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auto_applications",
    )
    job = models.ForeignKey(
        "jobs.JobListing", on_delete=models.CASCADE, related_name="auto_applications"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, default="auto")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-applied_at"]
        indexes = [models.Index(fields=["user", "applied_at"])]

    def __str__(self):
        return f"{self.user.email} → {self.job.title} [{self.status}]"
