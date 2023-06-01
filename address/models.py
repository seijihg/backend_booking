from django.db import models
from django_extensions.db.models import TimeStampedModel


# Create your models here.
class Address(TimeStampedModel):
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=255, blank=True)
