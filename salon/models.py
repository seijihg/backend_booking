from django.db import models
from django_extensions.db.models import TimeStampedModel

from address.models import Address
from booking_api.models import CommonInfo


# Create your models here.
class Salon(CommonInfo, TimeStampedModel):
    name = models.CharField(max_length=255)
    addresses = models.ManyToManyField(Address, blank=True)

    # SMS Settings
    reminder_time_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return self.name
