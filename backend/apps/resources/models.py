from django.conf import settings
from django.db import models


class Resource(models.Model):
    RESOURCE_TYPES = [
        ("article", "Article"),
        ("video", "Video"),
        ("course", "Course"),
        ("book", "Book"),
        ("tool", "Tool"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES, default="article")
    url = models.URLField()
    tags = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
