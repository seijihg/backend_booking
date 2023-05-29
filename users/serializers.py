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

    # def update(self, instance, validated_data):
    #     """
    #     Update and return an existing `User` instance, given the validated data.
    #     """
    #     email = validated_data.get("email")
    #     if email:

    #         exporter_user = ExtendedUser.objects.filter(
    #             email__iexact=email
    #         )
    #         if not exporter_user.exists():
    #             instance.baseuser_ptr.email = email
    #             instance.baseuser_ptr.save()
    #             instance.save()
    #     return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedUser
        exclude = ("password", "is_superuser", "groups", "user_permissions")
