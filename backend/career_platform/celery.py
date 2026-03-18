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
    # Scrape all job sources every 6 hours
    "scrape-all-jobs": {
        "task": "jobs.scrape_all_sources",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Purge expired jobs daily at 02:00 UTC
    "purge-expired-jobs": {
        "task": "jobs.purge_expired_listings",
        "schedule": crontab(minute=0, hour=2),
    },
    # Recompute all matches daily at 04:00 UTC
    "recompute-all-matches": {
        "task": "jobs.recompute_all_matches",
        "schedule": crontab(minute=0, hour=4),
    },
    # Auto-apply daily at 8 AM
    "auto-apply-daily": {
        "task": "auto_apply.run_auto_apply_for_all_users",
        "schedule": crontab(minute=0, hour=8),
    },
    # Weekly digest every Sunday at 9 AM
    "weekly-digest-sunday": {
        "task": "apps.notifications.tasks.send_weekly_digest",
        "schedule": crontab(minute=0, hour=9, day_of_week=0),
    },
}
