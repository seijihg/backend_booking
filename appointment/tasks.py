import logging

import arrow
import dramatiq
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


@dramatiq.actor
def send_sms_confirmation(booking_id):
    """SMS #1: Send confirmation (immediate)."""
    from appointment.models import Appointment

    try:
        appointment = Appointment.objects.select_related("customer", "salon").get(
            pk=booking_id
        )
    except Appointment.DoesNotExist:
        logger.warning(f"Appointment {booking_id} not found")
        return

    appointment_time = arrow.get(appointment.appointment_time)
    customer = appointment.customer.full_name or "Customer"

    body = (
        f"Hi {customer}, Your appointment at {appointment.salon.name} "
        f"has been confirmed for {appointment_time.format('YYYY-MM-DD')} "
        f"at {appointment_time.format('h:mm A')}. See you soon!"
    )

    client.messages.create(
        body=body,
        to=str(appointment.customer.phone_number),
        from_=settings.TWILIO_PHONE_NUMBER,
    )
    logger.info(f"Confirmation SMS sent for appointment {booking_id}")


@dramatiq.actor
def send_sms_reminder(booking_id, cancelled_info=None):
    """SMS #2: Send reminder X minutes before appointment."""
    from appointment.models import Appointment

    if cancelled_info:
        body = (
            f"Hi, We regret to inform you that your scheduled appointment "
            f"for {cancelled_info.get('time_date', 'N/A')} has been cancelled."
        )
        client.messages.create(
            body=body,
            to=cancelled_info["phone_number"],
            from_=settings.TWILIO_PHONE_NUMBER,
        )
        return

    try:
        appointment = Appointment.objects.select_related("customer", "salon").get(
            pk=booking_id
        )
    except Appointment.DoesNotExist:
        logger.warning(f"Appointment {booking_id} not found")
        return

    appointment_time = arrow.get(appointment.appointment_time)
    customer = appointment.customer.full_name or "Customer"

    body = (
        f"Hi {customer}, You have an appointment coming up "
        f"at {appointment_time.format('h:mm A')}. "
        f"Regards {appointment.salon.name}."
    )

    client.messages.create(
        body=body,
        to=str(appointment.customer.phone_number),
        from_=settings.TWILIO_PHONE_NUMBER,
    )
    logger.info(f"Reminder SMS sent for appointment {booking_id}")
