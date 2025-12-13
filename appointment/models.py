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

        # Only send SMS if customer has phone number
        if not self.customer.phone_number:
            return

        # SMS #1: Confirmation (new OR time changed)
        if is_new or time_changed:
            self.send_confirmation_sms()

        # SMS #2: Reminder (always schedule/reschedule)
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
