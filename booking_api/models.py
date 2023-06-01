from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.
class CommonInfo(models.Model):
    phone_number = PhoneNumberField(blank=True)

    class Meta:
        abstract = True
