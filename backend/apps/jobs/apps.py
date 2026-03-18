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

        # Preload the MiniLM sentence-transformer model so the first
        # match computation doesn't incur a cold-start delay.
        try:
            import time

            from apps.jobs.utils.matcher import get_model

            start = time.time()
            get_model()
            logger.info("MiniLM model loaded in %.2fs", time.time() - start)
        except ImportError:
            logger.warning(
                "sentence-transformers not installed, matching disabled"
            )
        except Exception as e:
            logger.warning("MiniLM model load failed: %s", e)
