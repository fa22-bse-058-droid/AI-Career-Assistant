"""
Resource Hub models.
"""
import uuid
from django.db import models


class Resource(models.Model):
    class Platform(models.TextChoices):
        COURSERA = "coursera", "Coursera"
        UDEMY = "udemy", "Udemy"
        YOUTUBE = "youtube", "YouTube"
        FREECODECAMP = "freecodecamp", "FreeCodeCamp"
        EDX = "edx", "edX"
        OTHER = "other", "Other"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    url = models.URLField()
    description = models.TextField(blank=True)
    skill_tags = models.JSONField(default=list)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices)
    is_free = models.BooleanField(default=True)
    duration_hours = models.FloatField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_free", "-rating"]

    def __str__(self):
        return f"{self.title} ({self.platform})"
