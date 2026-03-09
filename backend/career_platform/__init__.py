"""
career_platform package init — loads Celery app at startup.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)
