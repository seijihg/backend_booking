from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from booking_api.models import CommonInfo


# Create your models here.
class Salon(CommonInfo):
    name = models.CharField(max_length=255)
