from django.conf import settings
from django.db import models


class InterviewSession(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interview_sessions"
    )
    job_role = models.CharField(max_length=255)
    difficulty = models.CharField(
        max_length=20,
        choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
        default="medium",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    overall_score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} – {self.job_role} ({self.status})"


class InterviewQuestion(models.Model):
    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.TextField()
    user_answer = models.TextField(blank=True)
    ai_feedback = models.TextField(blank=True)
    score = models.FloatField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:60]}"
