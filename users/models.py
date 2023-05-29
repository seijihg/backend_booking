from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator

from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class CustomAccountManager(BaseUserManager):
    def _create_user(self, email, password, **kwargs):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("The given email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password, **kwargs):
        breakpoint()
        kwargs.setdefault("is_superuser", False)

        return self._create_user(email, password, **kwargs)

    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_owner", True)

        return self._create_user(email, password, **kwargs)


class ExtendedUser(AbstractUser, PermissionsMixin, TimeStampedModel):
    username_validator = UnicodeUsernameValidator()
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(default="")
    is_owner = models.BooleanField(
        default=False,
        help_text="Designates whether the user is the owner.",
    )
    username = None

    objects = CustomAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email
