from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from appointment.models import Appointment
from customer.models import Customer
from salon.models import Salon
from user.models import ExtendedUser


@pytest.fixture
def salon(db):
    """Create a test salon."""
    return Salon.objects.create(
        name="Test Salon",
        phone_number="+447700900000",
        reminder_time_minutes=60,
    )


@pytest.fixture
def user(db, salon):
    """Create an authenticated staff user linked to the salon."""
    u = ExtendedUser.objects.create_user(
        email="staff@test.com",
        password="testpass123",
        full_name="Test Staff",
    )
    u.salons.add(salon)
    return u


@pytest.fixture
def customer(db, salon):
    """Create a test customer linked to the salon."""
    c = Customer.objects.create(
        full_name="Ellie Smith",
        phone_number="+447700900123",
    )
    c.salons.add(salon)
    return c


@pytest.fixture
def existing_appointment(db, salon, user, customer):
    """Create an existing appointment for conflict testing.

    Scheduled for tomorrow +2h on column 2, duration 60 min.
    """
    start = timezone.now() + timedelta(days=1, hours=2)
    return Appointment.objects.create(
        salon=salon,
        user=user,
        customer=customer,
        appointment_time=start,
        end_time=start + timedelta(minutes=60),
        column_id=2,
    )


@pytest.fixture
def auth_client(user):
    """DRF API client with JWT authentication for the test user."""
    api_client = APIClient()
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client
