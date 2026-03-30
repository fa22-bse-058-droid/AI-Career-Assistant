"""
Test-specific Django settings — imports everything from the main settings
and overrides DATABASES to use an in-memory SQLite instance so tests can
run without a running MySQL / Docker stack.
"""
import os

# Provide defaults for any required env vars so the test suite can run
# without a full .env file or Docker stack.
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-used-in-production")

# Re-export everything from the main settings module
from career_platform.settings import *  # noqa: F401, F403, WPS433

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
