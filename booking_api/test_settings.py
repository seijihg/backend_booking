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
