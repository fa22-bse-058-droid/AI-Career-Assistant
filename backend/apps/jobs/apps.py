"""
Jobs app configuration.
"""
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobs"
    label = "jobs"

    def ready(self):
        # Register signal handlers
        import apps.jobs.signals  # noqa: F401
