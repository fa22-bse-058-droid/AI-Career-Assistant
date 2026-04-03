"""
career_platform package init.
"""

__all__ = ("celery_app",)


def __getattr__(name):
    """
    Lazily expose celery_app so importing career_platform doesn't trigger Celery
    autodiscovery during Django startup.
    """
    if name == "celery_app":
        from .celery import app as celery_app

        return celery_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
