from django.conf import settings
from django.db import models

from apps.jobs.models import JobListing


class Application(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("viewed", "Viewed"),
        ("interviewing", "Interviewing"),
        ("offered", "Offered"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    cover_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user.username} → {self.job.title} ({self.status})"
