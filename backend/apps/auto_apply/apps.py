"""
Auto-Apply app configuration.
"""
from django.apps import AppConfig


class AutoApplyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auto_apply"
    label = "auto_apply"
