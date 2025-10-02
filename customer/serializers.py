from typing import ClassVar

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from salon.serializers import SalonSerializer

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(region="GB")
    salons = SalonSerializer(many=True, read_only=True)
    salon_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=__import__('salon.models', fromlist=['Salon']).Salon.objects.all(),
        source='salons',
        required=True,
    )

    class Meta:
        model = Customer
        fields: ClassVar[list[str]] = [
            'id',
            'full_name',
            'phone_number',
            'salons',
            'salon_ids',
            'created',
            'modified',
        ]
        read_only_fields: ClassVar[list[str]] = ['created', 'modified']

    def validate_salon_ids(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "At least one salon must be assigned to the customer."
            )
        return value

    def create(self, validated_data):
        salons = validated_data.pop('salons', [])
        customer = Customer.objects.create(**validated_data)

        if salons:
            customer.salons.set(salons)

        return customer

    def update(self, instance, validated_data):
        salons = validated_data.pop('salons', None)

        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.phone_number = validated_data.get(
            'phone_number', instance.phone_number
        )
        instance.save()

        if salons is not None:
            instance.salons.set(salons)

        return instance
