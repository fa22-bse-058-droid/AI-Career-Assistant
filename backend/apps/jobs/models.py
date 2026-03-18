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

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        INTERNSHIP = "internship", "Internship"
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"

    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        MID = "mid", "Mid Level"
        SENIOR = "senior", "Senior Level"
        ANY = "any", "Any Level"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    experience_level = models.CharField(
        max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ANY
    )
    description = models.TextField()
    requirements = models.TextField(blank=True)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_display = models.CharField(max_length=100, blank=True)
    url = models.URLField(unique=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.ROZEE)
    scraped_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    skills_required = models.JSONField(default=list)
    raw_html = models.TextField(blank=True)

    class Meta:
        ordering = ["-scraped_at"]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["scraped_at"]),
            models.Index(fields=["job_type"]),
            models.Index(fields=["experience_level"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = (
                (self.scraped_at or timezone.now()) + timezone.timedelta(days=30)
            )
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def days_remaining(self) -> int:
        if not self.expires_at:
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    @property
    def formatted_salary(self) -> str:
        if self.salary_display:
            return self.salary_display
        if self.salary_min and self.salary_max:
            return f"PKR {self.salary_min:,} – {self.salary_max:,}"
        if self.salary_min:
            return f"PKR {self.salary_min:,}+"
        if self.salary_max:
            return f"Up to PKR {self.salary_max:,}"
        return "Not disclosed"


class JobApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPLIED = "applied", "Applied"
        INTERVIEWING = "interviewing", "Interviewing"
        REJECTED = "rejected", "Rejected"
        ACCEPTED = "accepted", "Accepted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="applications")
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    auto_applied = models.BooleanField(default=False)
    cover_letter = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [["user", "job"]]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user.email} → {self.job.title} [{self.status}]"


class ScraperRun(models.Model):
    class Source(models.TextChoices):
        ROZEE = "rozee", "Rozee.pk"
        INDEED = "indeed", "Indeed"
        ALL = "all", "All Sources"

    class TriggerType(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        MANUAL = "manual", "Manual"

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=20, choices=Source.choices)
    triggered_by = models.CharField(
        max_length=20, choices=TriggerType.choices, default=TriggerType.SCHEDULED
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    jobs_found = models.IntegerField(default=0)
    jobs_added = models.IntegerField(default=0)
    jobs_updated = models.IntegerField(default=0)
    jobs_skipped = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"[{self.source}] {self.status} — {self.started_at}"

    @property
    def duration_seconds(self) -> float:
        if not self.ended_at:
            return 0.0
        return (self.ended_at - self.started_at).total_seconds()


# Backward-compat alias used by admin_panel app
ScraperLog = ScraperRun


class UserJobMatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_matches",
    )
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="matches")
    score = models.FloatField()
    skill_overlap = models.JSONField(default=list)
    skill_overlap_count = models.IntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user", "job"]]
        ordering = ["-score"]

    def __str__(self):
        return f"{self.user.email} → {self.job.title}: {self.score:.2f}"

    @property
    def score_percentage(self) -> int:
        return round(self.score * 100)

    @property
    def match_label(self) -> str:
        if self.score >= 0.80:
            return "Excellent"
        if self.score >= 0.65:
            return "Good"
        if self.score >= 0.50:
            return "Fair"
        return "Low"


# Backward-compat alias used by auto_apply app (match_score field mapped to score)
class JobMatch(models.Model):
    """Deprecated: Use UserJobMatch. Kept as a proxy for backward compatibility."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="legacy_job_matches",
    )
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="legacy_matches")
    match_score = models.FloatField(default=0.0)
    semantic_score = models.FloatField(default=0.0)
    keyword_score = models.FloatField(default=0.0)
    is_bookmarked = models.BooleanField(default=False)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user", "job"]]
        ordering = ["-match_score"]

    def __str__(self):
        return f"{self.user.email} → {self.job.title}: {self.match_score:.2f}"


class SavedJob(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_jobs",
    )
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "job"]]
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"
