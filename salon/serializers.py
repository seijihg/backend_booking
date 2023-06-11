from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField

from address.models import Address
from address.serializers import AddressSerializer
from .models import Salon


class SalonSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True)
    phone_number = PhoneNumberField(region="GB")

    class Meta:
        model = Salon
        fields = "__all__"

    def validate_addresses(self, addresses):
        if len(addresses) == 0:
            raise serializers.ValidationError("Address cannot be an empty list.")
        return addresses

    def create(self, validated_data):
        address_data = validated_data.pop("addresses", [])
        salon = Salon.objects.create(**validated_data)

        for address in address_data:
            addr = Address.objects.create(salon=salon, **address)
            salon.addresses.add(addr)

        return salon
