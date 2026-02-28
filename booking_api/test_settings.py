import os

# Required env vars that settings.py reads at import time.
# Must be set BEFORE the import below. setdefault avoids overriding real values.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///dev-null")

from booking_api.settings import *  # noqa: F403

# Use SQLite for tests (no PostgreSQL dependency)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use in-memory cache (no Redis dependency)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use stub broker (no Redis dependency)
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.stub.StubBroker",
    "OPTIONS": {},
    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ],
}

# Dummy Twilio credentials (never actually called, mocked in conftest)
TWILIO_ACCOUNT_SID = "AC_test_sid"
TWILIO_AUTH_TOKEN = "test_auth_token"
TWILIO_PHONE_NUMBER = "+15005550006"

# Dummy OpenAI credentials (never actually called, mocked in tests)
OPENAI_API_KEY = "sk-test-key"
OPENAI_MODEL = "gpt-4o"
OPENAI_WHISPER_MODEL = "whisper-1"
