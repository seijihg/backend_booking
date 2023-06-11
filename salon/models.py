from django.db import models

from django_extensions.db.models import TimeStampedModel

from booking_api.models import CommonInfo
from address.models import Address


# Create your models here.
class Salon(CommonInfo, TimeStampedModel):
    name = models.CharField(max_length=255)
    addresses = models.ManyToManyField(Address, blank=True)

    def __str__(self):
        return self.name
