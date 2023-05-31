from typing import Dict

from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from dj_rest_auth.registration.serializers import RegisterSerializer

from .models import ExtendedUser


class UserCreateUpdateSerializer(RegisterSerializer):
    email = serializers.EmailField(
        error_messages={
            "invalid": "Enter an email address in the correct format, like name@example.com"
        }
    )
    phone_number = PhoneNumberField(required=False, allow_blank=True, region="GB")

    def clean_email(self, email):
        return email.lower() if email else None

    def save(self, request):
        user = super().save(request)
        user.phone_number = self.validated_data["phone_number"]
        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(required=False, allow_blank=True, region="GB")

    class Meta:
        model = ExtendedUser
        exclude = ("password", "is_superuser", "groups", "user_permissions")
