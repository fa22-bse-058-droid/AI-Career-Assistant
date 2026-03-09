"""
Notifications app models.
"""
import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        BADGE_EARNED = "badge_earned", "Badge Earned"
        JOB_MATCH = "job_match", "High Job Match"
        FORUM_REPLY = "forum_reply", "Forum Reply"
        AUTO_APPLY = "auto_apply", "Auto-Apply Done"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"[{self.type}] {self.title} → {self.user.email}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_enabled = models.BooleanField(default=True)
    on_site_enabled = models.BooleanField(default=True)
    weekly_digest_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Prefs for {self.user.email}"
