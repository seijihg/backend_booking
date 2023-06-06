import arrow
import dramatiq
from twilio.rest import Client
from django.conf import settings

from appointment.models import Appointment

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


@dramatiq.actor
def send_sms_reminder(booking_id):
    """Send a reminder to a phone using Twilio SMS"""
    # Get our appointment from the database
    try:
        appointment = Appointment.objects.get(pk=booking_id)
    except Appointment.DoesNotExist:
        # The appointment we were trying to remind someone about
        # has been deleted, so we don't need to do anything
        return

    breakpoint()
    appointment_time = arrow.get(appointment.appointment_time)
    customer = appointment.user.first_name

    if not customer:
        customer = "Customer"

    body = f'Hi {customer}. You have an appointment coming up at {appointment_time.format("YYYY-MM-DD h:mm a")}.'

    client.messages.create(
        body=body,
        to=str(appointment.user.phone_number),
        from_=settings.TWILIO_PHONE_NUMBER,
    )
