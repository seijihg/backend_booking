import arrow
from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel
import redis
from salon.models import Salon
from user.models import Customer, ExtendedUser


# Create your models here.
class Appointment(TimeStampedModel):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    user = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    appointment_time = models.DateTimeField()
    comment = models.TextField(blank=True, default="")

    # Additional fields not visible to users
    task_id = models.CharField(max_length=50, blank=True, editable=False)

    def __str__(self):
        return "Appointment #{0} - {1}".format(self.pk, self.user)

    def schedule_reminder(self):
        """Schedule a Dramatiq task to send a reminder for this appointment"""

        # Calculate the correct time to send this reminder
        appointment_time = arrow.get(self.appointment_time)
        reminder_time = appointment_time.shift(minutes=-5)
        now = arrow.now()
        milli_to_wait = int((reminder_time - now).total_seconds()) * 1000
        # Schedule the Dramatiq task
        from .tasks import send_sms_reminder

        result = send_sms_reminder.send_with_options(
            args=(self.pk,),
            # delay=milli_to_wait
        )

        return result.options["redis_message_id"]

    def cancel_task(self):
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.hdel("dramatiq:default.DQ.msgs", self.task_id)

    def save(self, *args, **kwargs):
        """Custom save method which also schedules a reminder"""

        # Check if we have scheduled a reminder for this appointment before
        if self.task_id:
            # Revoke that task in case its time has changed
            self.cancel_task()

        # Save our appointment, which populates self.pk,
        # which is used in schedule_reminder
        super().save(*args, **kwargs)

        if self.customer.phone_number:
            # Schedule a new reminder task for this appointment
            self.task_id = self.schedule_reminder()

            # Save our appointment again, with the new task_id
            Appointment.objects.filter(id=self.id).update(task_id=self.task_id)

    def delete_reminder(self):
        from .tasks import send_sms_reminder

        time_date = arrow.get(self.appointment_time).format("YYYY-MM-DD h:mm a")
        phone_number = str(self.customer.phone_number)
        result = send_sms_reminder.send(
            self.pk, {"time_date": time_date, "phone_number": phone_number}
        )

        return result.options["redis_message_id"]

    def delete(self, *args, **kwargs):
        if self.task_id:
            self.cancel_task()

        self.delete_reminder()

        super().delete(*args, **kwargs)
