from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

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

    def update(self, instance, validated_data):
        address_data = validated_data.pop("addresses", None)

        # Update salon fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update addresses if provided
        if address_data is not None:
            # Clear existing addresses and add new ones
            instance.addresses.clear()
            for address in address_data:
                address_id = address.get("id")
                if address_id:
                    # Update existing address
                    addr = Address.objects.filter(id=address_id).first()
                    if addr:
                        for attr, value in address.items():
                            if attr != "id":
                                setattr(addr, attr, value)
                        addr.save()
                        instance.addresses.add(addr)
                else:
                    # Create new address
                    addr = Address.objects.create(salon=instance, **address)
                    instance.addresses.add(addr)

        return instance
