"""
Jobs app configuration.
"""
import logging
import time

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobs"
    label = "jobs"

    def ready(self):
        """Lazy-load the SentenceTransformer model once per process at startup."""
        try:
            from apps.jobs.utils import matcher as _matcher_module
            start = time.time()
            model = _matcher_module.get_model()
            elapsed = time.time() - start
            if model is not None:
                logger.info(
                    "Jobs: SentenceTransformer loaded in %.2f s", elapsed
                )
            else:
                logger.warning(
                    "Jobs: SentenceTransformer could not be loaded — "
                    "job matching will be unavailable"
                )
        except ImportError as exc:
            logger.warning("Jobs: SentenceTransformer import error: %s", exc)
