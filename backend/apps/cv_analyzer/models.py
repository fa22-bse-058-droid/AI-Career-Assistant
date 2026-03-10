from django.conf import settings
from django.db import models


class CV(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cvs"
    )
    file = models.FileField(upload_to="cvs/")
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.username} – {self.original_filename}"


class CVAnalysis(models.Model):
    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name="analysis")
    score = models.FloatField(null=True, blank=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    keywords = models.JSONField(default=list)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.cv}"
