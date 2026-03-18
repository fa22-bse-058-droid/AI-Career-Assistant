"""
Signal handlers for the Jobs app.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="cv_analyzer.CVAnalysis")
def on_cv_analysis_saved(sender, instance, created, **kwargs):
    """Trigger job-match computation when a new CVAnalysis is created."""
    if not created:
        return

    # Local imports to avoid circular dependencies
    from apps.cv_analyzer.models import CVAnalysis  # noqa: F401
    from apps.jobs.tasks import compute_matches_for_user

    try:
        user_id = str(instance.cv.user.id)
        compute_matches_for_user.delay(user_id)
    except Exception as exc:
        logger.exception(
            "Failed to dispatch compute_matches_for_user for CVAnalysis %s: %s",
            instance.pk,
            exc,
        )
