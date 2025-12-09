# SMS Reminder Customization - Implementation Plan

## Overview

Implement a **two-SMS notification system** for appointments:

| SMS Type | When Sent | Purpose |
|----------|-----------|---------|
| **Confirmation SMS** | On booking OR when time changes | Confirm appointment time |
| **Reminder SMS** | X minutes before appointment (always) | Remind customer |

---

## Architecture

### SMS Flow

```
APPOINTMENT CREATED OR TIME CHANGED
              │
              ▼
     SMS #1: CONFIRMATION (immediate)
     "Your appointment has been confirmed for {date} at {time}"
              │
              ▼
     SMS #2: REMINDER (scheduled - always sent)
     "You have an appointment coming up at {time}"
```

---

## Database Schema

### Salon Model

```python
class Salon(CommonInfo, TimeStampedModel):
    name = models.CharField(max_length=255)
    addresses = models.ManyToManyField(Address, blank=True)

    # SMS Settings
    reminder_time_minutes = models.PositiveIntegerField(default=60)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `reminder_time_minutes` | `PositiveIntegerField` | `60` | Minutes before appointment |

---

## Code Changes

### 1. `salon/models.py`

```python
from django.db import models
from django_extensions.db.models import TimeStampedModel

from address.models import Address
from booking_api.models import CommonInfo


class Salon(CommonInfo, TimeStampedModel):
    name = models.CharField(max_length=255)
    addresses = models.ManyToManyField(Address, blank=True)

    # SMS Settings
    reminder_time_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return self.name
```

### 2. `appointment/tasks.py`

```python
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
```

### 3. `appointment/models.py`

```python
import arrow
import redis
from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel

from customer.models import Customer
from salon.models import Salon
from user.models import ExtendedUser


class Appointment(TimeStampedModel):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    user = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    appointment_time = models.DateTimeField()
    comment = models.TextField(blank=True, default="")
    column_id = models.IntegerField(default=1)
    end_time = models.DateTimeField(blank=True, null=True)
    task_id = models.CharField(max_length=50, blank=True, editable=False)

    def __str__(self):
        return f"Appointment #{self.pk} - {self.user}"

    def send_confirmation_sms(self):
        """SMS #1: Send immediate confirmation."""
        from .tasks import send_sms_confirmation

        send_sms_confirmation.send(self.pk)

    def schedule_reminder_sms(self):
        """SMS #2: Schedule reminder X minutes before."""
        reminder_minutes = self.salon.reminder_time_minutes
        appointment_time = arrow.get(self.appointment_time)
        reminder_time = appointment_time.shift(minutes=-reminder_minutes)
        now = arrow.now()

        milli_to_wait = int((reminder_time - now).total_seconds()) * 1000

        if milli_to_wait <= 0:
            return None

        from .tasks import send_sms_reminder

        result = send_sms_reminder.send_with_options(
            args=(self.pk,), delay=milli_to_wait
        )
        return result.options["redis_message_id"]

    def cancel_task(self):
        """Cancel scheduled reminder task."""
        if not self.task_id:
            return
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.hdel("dramatiq:default.DQ.msgs", self.task_id)

    def save(self, *args, **kwargs):
        """Handle SMS on create or time change."""
        is_new = self.pk is None
        time_changed = False

        if not is_new:
            old = Appointment.objects.get(pk=self.pk)
            time_changed = old.appointment_time != self.appointment_time

        # Cancel old reminder
        if self.task_id:
            self.cancel_task()

        super().save(*args, **kwargs)

        # SMS #1: Confirmation (new OR time changed)
        if is_new or time_changed:
            self.send_confirmation_sms()

        # SMS #2: Reminder (always)
        task_id = self.schedule_reminder_sms()
        if task_id:
            self.task_id = task_id
            Appointment.objects.filter(id=self.id).update(task_id=self.task_id)

    def delete(self, *args, **kwargs):
        """Cancel reminder and send cancellation SMS."""
        if self.task_id:
            self.cancel_task()

        from .tasks import send_sms_reminder

        time_date = arrow.get(self.appointment_time).format("YYYY-MM-DD h:mm A")
        send_sms_reminder.send(
            self.pk,
            {"time_date": time_date, "phone_number": str(self.customer.phone_number)},
        )

        super().delete(*args, **kwargs)
```

---

## API

### `PATCH /salons/{id}/`

```json
{
    "reminder_time_minutes": 120
}
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `salon/models.py` | Add `reminder_time_minutes` field |
| `appointment/models.py` | Update save() |
| `appointment/tasks.py` | Add send_sms_confirmation |

---

## Run

```bash
docker compose run --rm web python manage.py makemigrations salon --name add_sms_settings
docker compose run --rm web python manage.py migrate salon
```
