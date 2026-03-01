import json
import logging
from datetime import datetime, timedelta

from django.utils import timezone

from appointment.models import Appointment
from customer.models import Customer

logger = logging.getLogger(__name__)


def execute_tool_call(tool_name, arguments, salon, user):
    """Dispatch a GPT-4 tool call to the appropriate handler.

    Returns a JSON string (always), so GPT-4 can read the result.
    """
    handlers = {
        "lookup_customer": _handle_lookup_customer,
        "create_customer": _handle_create_customer,
        "check_availability": _handle_check_availability,
        "create_appointment": _handle_create_appointment,
    }
    handler = handlers.get(tool_name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return handler(arguments, salon, user)
    except Exception:
        logger.exception("Tool %s failed", tool_name)
        return json.dumps({"error": f"Tool '{tool_name}' failed unexpectedly."})


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _handle_lookup_customer(args, salon, user):
    phone_number = args.get("phone_number", "")
    customer = Customer.objects.filter(salons=salon, phone_number=phone_number).first()
    if customer:
        return json.dumps(
            {
                "found": True,
                "customer_id": customer.id,
                "full_name": customer.full_name,
                "phone_number": str(customer.phone_number),
            }
        )
    return json.dumps(
        {
            "found": False,
            "message": f"No customer found with phone number {phone_number} in this salon.",
        }
    )


def _handle_create_customer(args, salon, user):
    full_name = args.get("full_name", "")
    phone_number = args.get("phone_number", "")

    existing = Customer.objects.filter(salons=salon, phone_number=phone_number).first()
    if existing:
        return json.dumps(
            {
                "created": False,
                "customer_id": existing.id,
                "full_name": existing.full_name,
                "phone_number": str(existing.phone_number),
                "message": "Customer already exists.",
            }
        )

    customer = Customer.objects.create(full_name=full_name, phone_number=phone_number)
    customer.salons.add(salon)
    return json.dumps(
        {
            "created": True,
            "customer_id": customer.id,
            "full_name": customer.full_name,
            "phone_number": str(customer.phone_number),
        }
    )


def _handle_check_availability(args, salon, user):
    date_str = args.get("date", "")
    time_str = args.get("time", "")
    duration = args.get("duration_minutes", 60)
    column_id = args.get("column_id")

    if duration % 15 != 0:
        return json.dumps({"error": "Duration must be a multiple of 15 minutes."})

    try:
        naive_start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        start_dt = timezone.make_aware(naive_start)
    except (ValueError, TypeError):
        return json.dumps({"error": f"Invalid date/time format: {date_str} {time_str}"})

    end_dt = start_dt + timedelta(minutes=duration)
    columns_to_check = [column_id] if column_id else [1, 2, 3, 4, 5]

    available_columns = []
    busy_columns = {}

    for col in columns_to_check:
        conflicts = _find_conflicts(salon, col, start_dt, end_dt)
        if conflicts:
            busy_columns[col] = conflicts
        else:
            available_columns.append(col)

    return json.dumps(
        {
            "available_columns": available_columns,
            "busy_columns": busy_columns,
        }
    )


def _find_conflicts(salon, column_id, start_dt, end_dt):
    """Find overlapping appointments for a given column and time range."""
    appointments = Appointment.objects.filter(
        salon=salon,
        column_id=column_id,
        appointment_time__date=start_dt.date(),
    )

    conflicts = []
    for appt in appointments:
        appt_start = appt.appointment_time.replace(second=0, microsecond=0)
        appt_end = appt.end_time or (appt.appointment_time + timedelta(minutes=60))
        appt_end = appt_end.replace(second=0, microsecond=0)

        # Overlap: existing.start < requested.end AND existing.end > requested.start
        if appt_start < end_dt and appt_end > start_dt:
            conflicts.append(
                f"{appt_start.strftime('%H:%M')}-{appt_end.strftime('%H:%M')}"
            )
    return conflicts


def _handle_create_appointment(args, salon, user):
    customer_id = args.get("customer_id")
    phone_number = args.get("phone_number", "")
    appointment_time_str = args.get("appointment_time", "")
    duration = args.get("duration_minutes", 60)
    column_id = args.get("column_id")
    comment = args.get("comment", "")

    # Validate column
    if not column_id or column_id < 1 or column_id > 5:
        return json.dumps({"error": "column_id must be between 1 and 5."})

    # Validate duration
    if duration % 15 != 0:
        return json.dumps({"error": "Duration must be a multiple of 15 minutes."})

    # Parse time
    try:
        start_dt = datetime.fromisoformat(appointment_time_str)
        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
    except (ValueError, TypeError):
        return json.dumps(
            {"error": f"Invalid appointment_time format: {appointment_time_str}"}
        )

    # Reject past times
    if start_dt < timezone.now():
        return json.dumps({"error": "Cannot book appointments in the past."})

    # Validate customer belongs to salon
    try:
        customer = Customer.objects.get(id=customer_id, salons=salon)
    except Customer.DoesNotExist:
        return json.dumps({"error": f"Customer {customer_id} not found in this salon."})

    # Cross-check phone number matches customer record
    if phone_number and str(customer.phone_number) != phone_number:
        return json.dumps(
            {
                "error": (
                    f"Phone number mismatch: customer {customer_id} has "
                    f"{customer.phone_number}, not {phone_number}. "
                    f"Use the correct customer_id."
                ),
            }
        )

    end_dt = start_dt + timedelta(minutes=duration)

    appointment = Appointment(
        salon=salon,
        user=user,
        customer=customer,
        appointment_time=start_dt,
        end_time=end_dt,
        column_id=column_id,
        comment=comment,
    )
    appointment.save()

    return json.dumps(
        {
            "created": True,
            "appointment_id": appointment.id,
            "message": (
                f"Appointment booked for {customer.full_name} on "
                f"{start_dt.strftime('%Y-%m-%d at %H:%M')} "
                f"(column {column_id}, {duration} minutes)."
            ),
        }
    )
