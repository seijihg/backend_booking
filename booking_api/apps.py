"""
Django app configuration for booking_api.
"""

from django.apps import AppConfig


class BookingApiConfig(AppConfig):
    """Configuration class for the booking_api application."""

    name = "booking_api"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Run once at Django startup.

        This method is called when Django starts and is used to perform
        one-time initialization tasks like health checks for external services.
        """
        # Import here to avoid AppRegistryNotReady error
        # Only run health checks if not running migrations or other management commands
        # that don't need external services
        import sys

        from .healthchecks import run_startup_health_checks

        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            run_startup_health_checks()
