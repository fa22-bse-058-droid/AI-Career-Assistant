"""
Celery tasks for notifications.
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="notifications.create_notification")
def create_notification(user_id: str, notif_type: str, title: str, message: str, link: str = ""):
    """Create an on-site notification and optionally send email."""
    from .models import Notification, NotificationPreference
    from apps.authentication.models import CustomUser

    try:
        user = CustomUser.objects.get(pk=user_id)
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)

        if prefs.on_site_enabled:
            Notification.objects.create(
                user=user, type=notif_type, title=title, message=message, link=link
            )

        if prefs.email_enabled:
            send_notification_email.delay(user_id, title, message)

    except Exception as e:
        logger.error("create_notification failed for user %s: %s", user_id, e)


@shared_task(name="notifications.send_notification_email")
def send_notification_email(user_id: str, subject: str, body: str):
    from apps.authentication.models import CustomUser

    try:
        user = CustomUser.objects.get(pk=user_id)
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error("Email send failed for user %s: %s", user_id, e)


@shared_task(name="notifications.send_weekly_digest")
def send_weekly_digest():
    """Send weekly digest to all users who opted in."""
    from .models import Notification, NotificationPreference
    from apps.authentication.models import CustomUser

    prefs = NotificationPreference.objects.filter(
        weekly_digest_enabled=True, email_enabled=True
    ).select_related("user")

    week_ago = timezone.now() - timezone.timedelta(days=7)

    for pref in prefs:
        notifs = Notification.objects.filter(
            user=pref.user, created_at__gte=week_ago
        ).order_by("-created_at")[:10]

        if not notifs:
            continue

        body = "Your weekly career assistant summary:\n\n"
        for n in notifs:
            body += f"• {n.title}: {n.message}\n"

        send_notification_email.delay(str(pref.user.id), "Your Weekly Career Digest", body)
