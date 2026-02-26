from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _disable_sms():
    """Prevent SMS sending and Dramatiq task interactions during all tests."""
    with (
        patch("appointment.models.Appointment.send_confirmation_sms"),
        patch(
            "appointment.models.Appointment.schedule_reminder_sms", return_value=None
        ),
        patch("appointment.models.Appointment.cancel_task"),
    ):
        yield
