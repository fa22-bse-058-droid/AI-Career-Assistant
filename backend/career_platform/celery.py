"""
Celery configuration for career_platform.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "career_platform.settings")

app = Celery("career_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    # Scrape jobs every 6 hours
    "scrape-jobs-every-6-hours": {
        "task": "apps.jobs.tasks.scrape_all_sources",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Purge expired jobs daily at 2 AM
    "purge-expired-jobs-daily": {
        "task": "apps.jobs.tasks.purge_expired_jobs",
        "schedule": crontab(minute=0, hour=2),
    },
    # Auto-apply daily at 8 AM
    "auto-apply-daily": {
        "task": "apps.auto_apply.tasks.run_auto_apply_for_all_users",
        "schedule": crontab(minute=0, hour=8),
    },
    # Weekly digest every Sunday at 9 AM
    "weekly-digest-sunday": {
        "task": "apps.notifications.tasks.send_weekly_digest",
        "schedule": crontab(minute=0, hour=9, day_of_week=0),
    },
}
