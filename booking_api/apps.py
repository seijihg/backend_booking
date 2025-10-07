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
        one-time initialization tasks.
        """
        # Import signal handlers or other startup code here if needed
        pass
