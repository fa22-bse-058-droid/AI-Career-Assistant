"""
Job listing models.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class JobListing(models.Model):
    class Source(models.TextChoices):
        ROZEE = "rozee", "Rozee.pk"
        INDEED = "indeed", "Indeed"
        LINKEDIN = "linkedin", "LinkedIn"
        MANUAL = "manual", "Manual"

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"
        REMOTE = "remote", "Remote"

    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        MID = "mid", "Mid Level"
        SENIOR = "senior", "Senior Level"
        LEAD = "lead", "Lead / Manager"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    experience_level = models.CharField(
        max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY
    )
    skills_required = models.JSONField(default=list)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-scraped_at"]
        indexes = [
            models.Index(fields=["scraped_at", "is_active"]),
            models.Index(fields=["source"]),
            models.Index(fields=["job_type"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = (
                (self.scraped_at or timezone.now()) + timezone.timedelta(days=30)
            )
        super().save(*args, **kwargs)


class JobMatch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_matches",
    )
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="matches")
    match_score = models.FloatField()
    semantic_score = models.FloatField(default=0.0)
    keyword_score = models.FloatField(default=0.0)
    is_bookmarked = models.BooleanField(default=False)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user", "job"]]
        ordering = ["-match_score"]

    def __str__(self):
        return f"{self.user.email} → {self.job.title}: {self.match_score:.2f}"


class ScraperLog(models.Model):
    class ScraperStatus(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    source = models.CharField(max_length=20, choices=JobListing.Source.choices)
    status = models.CharField(max_length=20, choices=ScraperStatus.choices)
    jobs_found = models.IntegerField(default=0)
    jobs_added = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"[{self.source}] {self.status} — {self.started_at}"
