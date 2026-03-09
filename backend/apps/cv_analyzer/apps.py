"""
CV Analyzer app configuration.
"""
from django.apps import AppConfig


class CVAnalyzerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cv_analyzer"
    label = "cv_analyzer"
