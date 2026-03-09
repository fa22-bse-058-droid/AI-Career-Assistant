"""
Mock Interview models.
"""
import uuid
from django.db import models
from django.conf import settings


class InterviewQuestion(models.Model):
    class Domain(models.TextChoices):
        SOFTWARE_ENGINEERING = "software_engineering", "Software Engineering"
        DATA_SCIENCE = "data_science", "Data Science"
        WEB_DEVELOPMENT = "web_development", "Web Development"
        SYSTEM_DESIGN = "system_design", "System Design"
        BEHAVIORAL = "behavioral", "Behavioral"
        DATABASES = "databases", "Databases"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.CharField(max_length=30, choices=Domain.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    question_text = models.TextField()
    expected_keywords = models.JSONField(default=list)
    model_answer = models.TextField()
    follow_up_questions = models.JSONField(default=list)

    class Meta:
        ordering = ["domain", "difficulty"]

    def __str__(self):
        return f"[{self.domain}/{self.difficulty}] {self.question_text[:80]}"


class InterviewSession(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    class Grade(models.TextChoices):
        POOR = "poor", "Poor (0-40)"
        AVERAGE = "average", "Average (41-60)"
        GOOD = "good", "Good (61-80)"
        EXCELLENT = "excellent", "Excellent (81-100)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )
    domain = models.CharField(max_length=30, choices=InterviewQuestion.Domain.choices)
    difficulty = models.CharField(
        max_length=10, choices=InterviewQuestion.Difficulty.choices
    )
    total_score = models.FloatField(default=0.0)
    grade = models.CharField(max_length=20, choices=Grade.choices, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Session {self.id} — {self.user.email} [{self.status}]"


class InterviewResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="responses"
    )
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE)
    user_response = models.TextField()
    score = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True)
    is_follow_up = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.question} — Score: {self.score:.1f}"
