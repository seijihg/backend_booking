import json
from datetime import timedelta

import pytest
from django.utils import timezone

from appointment.models import Appointment
from booking_api.voice.tool_executor import execute_tool_call
from customer.models import Customer
from salon.models import Salon

# ---------------------------------------------------------------------------
# lookup_customer
# ---------------------------------------------------------------------------


class TestLookupCustomer:
    @pytest.mark.django_db
    def test_finds_existing_customer(self, salon, user, customer):
        result = json.loads(
            execute_tool_call(
                "lookup_customer",
                {"phone_number": "+447700900123"},
                salon,
                user,
            )
        )
        assert result["found"] is True
        assert result["customer_id"] == customer.id
        assert result["full_name"] == "Ellie Smith"

    @pytest.mark.django_db
    def test_not_found(self, salon, user):
        result = json.loads(
            execute_tool_call(
                "lookup_customer",
                {"phone_number": "+447700999999"},
                salon,
                user,
            )
        )
        assert result["found"] is False

    @pytest.mark.django_db
    def test_scoped_to_salon(self, user, customer):
        """Customer in salon A should NOT be found when searching in salon B."""
        other_salon = Salon.objects.create(
            name="Other Salon", phone_number="+447700900999"
        )
        result = json.loads(
            execute_tool_call(
                "lookup_customer",
                {"phone_number": "+447700900123"},
                other_salon,
                user,
            )
        )
        assert result["found"] is False

    @pytest.mark.django_db
    def test_invalid_phone_format(self, salon, user):
        result = json.loads(
            execute_tool_call(
                "lookup_customer",
                {"phone_number": "not-a-phone"},
                salon,
                user,
            )
        )
        assert result["found"] is False


# ---------------------------------------------------------------------------
# create_customer
# ---------------------------------------------------------------------------


class TestCreateCustomer:
    @pytest.mark.django_db
    def test_create_new_customer(self, salon, user):
        result = json.loads(
            execute_tool_call(
                "create_customer",
                {"full_name": "New Person", "phone_number": "+447700900456"},
                salon,
                user,
            )
        )
        assert result["created"] is True
        assert Customer.objects.filter(phone_number="+447700900456").exists()
        created = Customer.objects.get(id=result["customer_id"])
        assert created.salons.filter(id=salon.id).exists()

    @pytest.mark.django_db
    def test_returns_existing_if_duplicate(self, salon, user, customer):
        result = json.loads(
            execute_tool_call(
                "create_customer",
                {"full_name": "Ellie Smith", "phone_number": "+447700900123"},
                salon,
                user,
            )
        )
        assert result["created"] is False
        assert result["customer_id"] == customer.id

    @pytest.mark.django_db
    def test_adds_salon_association(self, salon, user):
        result = json.loads(
            execute_tool_call(
                "create_customer",
                {"full_name": "Another Person", "phone_number": "+447700900789"},
                salon,
                user,
            )
        )
        created = Customer.objects.get(id=result["customer_id"])
        assert created.salons.filter(id=salon.id).exists()


# ---------------------------------------------------------------------------
# check_availability
# ---------------------------------------------------------------------------


class TestCheckAvailability:
    @pytest.mark.django_db
    def test_all_columns_free(self, salon, user):
        """No appointments at all — all 5 columns should be available."""
        tomorrow = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {"date": tomorrow, "time": "10:00", "duration_minutes": 60},
                salon,
                user,
            )
        )
        assert result["available_columns"] == [1, 2, 3, 4, 5]

    @pytest.mark.django_db
    def test_one_column_busy(self, salon, user, existing_appointment):
        """existing_appointment is on column 2. Others should be free."""
        appt_date = existing_appointment.appointment_time.strftime("%Y-%m-%d")
        appt_time = existing_appointment.appointment_time.strftime("%H:%M")

        result = json.loads(
            execute_tool_call(
                "check_availability",
                {"date": appt_date, "time": appt_time, "duration_minutes": 60},
                salon,
                user,
            )
        )
        assert 2 not in result["available_columns"]
        assert 1 in result["available_columns"]
        busy_keys = [int(k) for k in result["busy_columns"]]
        assert 2 in busy_keys

    @pytest.mark.django_db
    def test_specific_column_free(self, salon, user):
        """Query a specific column with no conflicts."""
        tomorrow = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {"date": tomorrow, "time": "10:00", "column_id": 3},
                salon,
                user,
            )
        )
        assert result["available_columns"] == [3]

    @pytest.mark.django_db
    def test_specific_column_busy(self, salon, user, existing_appointment):
        """Query the exact column that has the appointment."""
        appt_date = existing_appointment.appointment_time.strftime("%Y-%m-%d")
        appt_time = existing_appointment.appointment_time.strftime("%H:%M")

        result = json.loads(
            execute_tool_call(
                "check_availability",
                {
                    "date": appt_date,
                    "time": appt_time,
                    "column_id": existing_appointment.column_id,
                },
                salon,
                user,
            )
        )
        assert result["available_columns"] == []

    @pytest.mark.django_db
    def test_overlap_start_inside_existing(self, salon, user, existing_appointment):
        """Query starts 30 min into existing appointment — should be busy."""
        start = existing_appointment.appointment_time + timedelta(minutes=30)
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {
                    "date": start.strftime("%Y-%m-%d"),
                    "time": start.strftime("%H:%M"),
                    "duration_minutes": 30,
                    "column_id": existing_appointment.column_id,
                },
                salon,
                user,
            )
        )
        assert existing_appointment.column_id not in result["available_columns"]

    @pytest.mark.django_db
    def test_overlap_end_inside_existing(self, salon, user, existing_appointment):
        """Query starts 30 min before existing and runs 60 min — overlaps."""
        start = existing_appointment.appointment_time - timedelta(minutes=30)
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {
                    "date": start.strftime("%Y-%m-%d"),
                    "time": start.strftime("%H:%M"),
                    "duration_minutes": 60,
                    "column_id": existing_appointment.column_id,
                },
                salon,
                user,
            )
        )
        assert existing_appointment.column_id not in result["available_columns"]

    @pytest.mark.django_db
    def test_adjacent_not_overlapping(self, salon, user, existing_appointment):
        """Appointment ending at X, query starting at X — should be free."""
        end_time = existing_appointment.end_time
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {
                    "date": end_time.strftime("%Y-%m-%d"),
                    "time": end_time.strftime("%H:%M"),
                    "duration_minutes": 60,
                    "column_id": existing_appointment.column_id,
                },
                salon,
                user,
            )
        )
        assert existing_appointment.column_id in result["available_columns"]

    @pytest.mark.django_db
    def test_null_end_time_assumes_60min(self, salon, user, customer):
        """Appointment with null end_time should be treated as 60 min."""
        start = timezone.now() + timedelta(days=1, hours=4)
        Appointment.objects.create(
            salon=salon,
            user=user,
            customer=customer,
            appointment_time=start,
            end_time=None,
            column_id=1,
        )
        query_time = start + timedelta(minutes=30)
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {
                    "date": query_time.strftime("%Y-%m-%d"),
                    "time": query_time.strftime("%H:%M"),
                    "duration_minutes": 30,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        assert 1 not in result["available_columns"]

    @pytest.mark.django_db
    def test_invalid_duration_not_multiple_of_15(self, salon, user):
        tomorrow = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {"date": tomorrow, "time": "10:00", "duration_minutes": 25},
                salon,
                user,
            )
        )
        assert "error" in result

    @pytest.mark.django_db
    def test_invalid_date_format(self, salon, user):
        result = json.loads(
            execute_tool_call(
                "check_availability",
                {"date": "tomorrow", "time": "10:00"},
                salon,
                user,
            )
        )
        assert "error" in result

    @pytest.mark.django_db
    def test_default_duration_60(self, salon, user, existing_appointment):
        """Without duration_minutes, should default to 60."""
        appt_date = existing_appointment.appointment_time.strftime("%Y-%m-%d")
        appt_time = existing_appointment.appointment_time.strftime("%H:%M")

        result = json.loads(
            execute_tool_call(
                "check_availability",
                {"date": appt_date, "time": appt_time},
                salon,
                user,
            )
        )
        # Column 2 should be busy with default 60 min
        assert 2 not in result["available_columns"]


# ---------------------------------------------------------------------------
# create_appointment
# ---------------------------------------------------------------------------


class TestCreateAppointment:
    @pytest.mark.django_db
    def test_success(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "duration_minutes": 30,
                    "column_id": 3,
                    "comment": "Haircut",
                },
                salon,
                user,
            )
        )
        assert result["created"] is True
        appt = Appointment.objects.get(id=result["appointment_id"])
        assert appt.column_id == 3
        assert appt.customer == customer
        assert appt.comment == "Haircut"
        assert appt.end_time == appt.appointment_time + timedelta(minutes=30)

    @pytest.mark.django_db
    def test_correct_end_time(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "duration_minutes": 45,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        appt = Appointment.objects.get(id=result["appointment_id"])
        assert appt.end_time == appt.appointment_time + timedelta(minutes=45)

    @pytest.mark.django_db
    def test_default_duration_60(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        appt = Appointment.objects.get(id=result["appointment_id"])
        assert appt.end_time == appt.appointment_time + timedelta(minutes=60)

    @pytest.mark.django_db
    def test_rejects_past_time(self, salon, user, customer):
        past_time = (timezone.now() - timedelta(hours=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": past_time,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        assert "error" in result

    @pytest.mark.django_db
    def test_rejects_invalid_column(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "column_id": 6,
                },
                salon,
                user,
            )
        )
        assert "error" in result

    @pytest.mark.django_db
    def test_rejects_customer_not_in_salon(self, salon, user):
        other_salon = Salon.objects.create(name="Other", phone_number="+447700900999")
        other_customer = Customer.objects.create(
            full_name="Other Person", phone_number="+447700900555"
        )
        other_customer.salons.add(other_salon)

        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": other_customer.id,
                    "appointment_time": future_time,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        assert "error" in result

    @pytest.mark.django_db
    def test_rejects_invalid_duration(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "duration_minutes": 25,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        assert "error" in result

    @pytest.mark.django_db
    def test_saves_comment(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "column_id": 2,
                    "comment": "Gel nails",
                },
                salon,
                user,
            )
        )
        appt = Appointment.objects.get(id=result["appointment_id"])
        assert appt.comment == "Gel nails"

    @pytest.mark.django_db
    def test_appointment_saved_to_db(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447700900123",
                    "appointment_time": future_time,
                    "column_id": 4,
                },
                salon,
                user,
            )
        )
        assert Appointment.objects.filter(id=result["appointment_id"]).exists()

    @pytest.mark.django_db
    def test_rejects_phone_number_mismatch(self, salon, user, customer):
        future_time = (timezone.now() + timedelta(days=1)).isoformat()
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": customer.id,
                    "phone_number": "+447999999999",
                    "appointment_time": future_time,
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        assert "error" in result
        assert "mismatch" in result["error"].lower()
        assert not Appointment.objects.filter(customer=customer).exists()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class TestDispatcher:
    @pytest.mark.django_db
    def test_unknown_tool_returns_error(self, salon, user):
        result = json.loads(execute_tool_call("delete_everything", {}, salon, user))
        assert "error" in result

    @pytest.mark.django_db
    def test_exception_in_handler_returns_error(self, salon, user):
        """Passing bad data should return an error dict, not raise."""
        result = json.loads(
            execute_tool_call(
                "create_appointment",
                {
                    "customer_id": 999999,
                    "appointment_time": "not-a-datetime",
                    "column_id": 1,
                },
                salon,
                user,
            )
        )
        assert "error" in result
