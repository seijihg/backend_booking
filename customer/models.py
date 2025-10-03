from django.db import models
from django_extensions.db.models import TimeStampedModel

from booking_api.models import CommonInfo
from salon.models import Salon


# Create your models here.
class Customer(CommonInfo, TimeStampedModel):
    full_name = models.CharField(max_length=150, blank=True)
    salons = models.ManyToManyField(Salon, related_name='customers')

    def __str__(self):
        return self.full_name or str(self.phone_number)
