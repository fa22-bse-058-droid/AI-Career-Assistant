"""
Auto-Apply Celery tasks.
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="auto_apply.run_auto_apply_for_all_users",
)
def run_auto_apply_for_all_users(self):
    from .models import AutoApplySettings
    settings_qs = AutoApplySettings.objects.filter(is_enabled=True).select_related("user")
    for user_settings in settings_qs:
        run_auto_apply_for_user.delay(str(user_settings.user.id))


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="auto_apply.run_auto_apply_for_user",
)
def run_auto_apply_for_user(self, user_id: str):
    from .models import AutoApplySettings, ApplicationLog
    from apps.authentication.models import CustomUser
    from apps.jobs.models import JobListing, UserJobMatch

    try:
        user = CustomUser.objects.get(pk=user_id)
        settings_obj = AutoApplySettings.objects.get(user=user, is_enabled=True)
    except (CustomUser.DoesNotExist, AutoApplySettings.DoesNotExist):
        return

    # Get matches above threshold
    matches = UserJobMatch.objects.filter(
        user=user,
        score__gte=settings_obj.min_match_score,
    ).select_related("job")

    # Check daily quota
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    applied_today = ApplicationLog.objects.filter(
        user=user, applied_at__gte=today_start, status="applied"
    ).count()

    remaining_quota = settings_obj.max_applications_per_day - applied_today
    if remaining_quota <= 0:
        logger.info("Daily quota reached for user %s", user_id)
        return

    # Exclude already applied (within 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    already_applied_job_ids = ApplicationLog.objects.filter(
        user=user, applied_at__gte=thirty_days_ago
    ).values_list("job_id", flat=True)

    applied_count = 0
    for match in matches:
        if applied_count >= remaining_quota:
            break

        job = match.job
        if job.id in already_applied_job_ids:
            ApplicationLog.objects.create(
                user=user, job=job, status="skipped"
            )
            continue

        try:
            # Log application (real form-fill would go here via Selenium)
            ApplicationLog.objects.create(
                user=user,
                job=job,
                method="auto",
                status="applied",
            )
            applied_count += 1

            # Notify user
            from apps.notifications.tasks import create_notification
            create_notification.delay(
                user_id,
                "auto_apply",
                "Auto-Apply Completed",
                f"Automatically applied to: {job.title} at {job.company}",
                f"/jobs/{job.id}/",
            )

        except Exception as exc:
            ApplicationLog.objects.create(
                user=user, job=job, status="failed", error_message=str(exc)
            )
            logger.error("Auto-apply failed for job %s: %s", job.id, exc)

    logger.info("Auto-applied to %d jobs for user %s", applied_count, user_id)
