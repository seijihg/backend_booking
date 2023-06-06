import arrow
from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel
import redis
from salon.models import Salon
from user.models import ExtendedUser


# Create your models here.
class Appointment(TimeStampedModel):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    user = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE)
    appointment_time = models.DateTimeField()

    # Additional fields not visible to users
    task_id = models.CharField(max_length=50, blank=True, editable=False)

    def __str__(self):
        return "Appointment #{0} - {1}".format(self.pk, self.user)

    def schedule_reminder(self):
        """Schedule a Dramatiq task to send a reminder for this appointment"""

        # Calculate the correct time to send this reminder
        appointment_time = arrow.get(self.date_time, self.time_zone.zone)
        reminder_time = appointment_time.shift(minutes=-5)
        now = arrow.now(self.time_zone.zone)
        milli_to_wait = int((reminder_time - now).total_seconds()) * 1000
        # Schedule the Dramatiq task
        from .tasks import send_sms_reminder

        result = send_sms_reminder.send_with_options(args=(self.pk,))

        return result.options["redis_message_id"]

    def cancel_task(self):
        redis_client = redis.Redis(host=settings.REDIS_URL, port=6379, db=0)
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

        # Schedule a new reminder task for this appointment
        self.task_id = self.schedule_reminder()

        # Save our appointment again, with the new task_id
        Appointment.objects.filter(id=self.id).update(task_id=self.task_id)