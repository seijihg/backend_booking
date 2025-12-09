from dj_rest_auth.registration.serializers import RegisterSerializer
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from salon.models import Salon

from .models import ExtendedUser


class UserCreateSerializer(RegisterSerializer):
    username = None  # Remove username field since we use email-only authentication
    email = serializers.EmailField(
        error_messages={
            "invalid": "Enter an email address in the correct format, like name@example.com"
        }
    )
    phone_number = PhoneNumberField(required=True, allow_blank=False, region="GB")
    salons = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of salon IDs the user belongs to",
    )

    def validate_email(self, email):
        return email.lower()

    def validate_salons(self, value):
        if value:
            existing_salon_ids = set(
                Salon.objects.filter(pk__in=value).values_list('pk', flat=True)
            )
            invalid_ids = set(value) - existing_salon_ids
            if invalid_ids:
                raise serializers.ValidationError(
                    f"Salon IDs {invalid_ids} do not exist"
                )
        return value

    def save(self, request=None, **kwargs):
        user = super().save(request, **kwargs)

        user.phone_number = self.validated_data["phone_number"]
        user.save()

        # Add user to salons if provided
        if "salons" in self.validated_data and self.validated_data["salons"]:
            salon_ids = self.validated_data["salons"]
            salons = Salon.objects.filter(pk__in=salon_ids)
            user.salons.set(salons)

        return user


class UserSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(required=True, allow_blank=False, region="GB")
    salons = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = ExtendedUser
        exclude = ("password", "is_superuser", "groups", "user_permissions")
