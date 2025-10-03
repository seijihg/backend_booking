import os

from django.core.management.base import BaseCommand
from django.db import transaction

from address.models import Address
from salon.models import Salon
from user.models import ExtendedUser


class Command(BaseCommand):
    help = 'Seeds the database with initial salon and user data using environment variables'

    def handle(self, *args, **options):
        self.stdout.write('Starting database seeding...')

        # Get seed data from environment variables
        salon_name = os.environ.get('SEED_SALON_NAME', 'Default Salon')
        salon_phone_number = os.environ.get('SEED_SALON_PHONE_NUMBER', '+447700900000')
        salon_street = os.environ.get('SEED_SALON_STREET', '123 Default St')
        salon_city = os.environ.get('SEED_SALON_CITY', 'London')
        salon_postal_code = os.environ.get('SEED_SALON_POSTAL_CODE', 'SW1A 1AA')

        owner_email = os.environ.get('SEED_OWNER_EMAIL', 'owner@example.com')
        owner_phone_number = os.environ.get('SEED_OWNER_PHONE_NUMBER', '+447700900001')
        owner_first_name = os.environ.get('SEED_OWNER_FIRST_NAME', 'Default')
        owner_last_name = os.environ.get('SEED_OWNER_LAST_NAME', 'Owner')
        owner_full_name = os.environ.get('SEED_OWNER_FULL_NAME', 'Default Owner')
        owner_password = os.environ.get('SEED_OWNER_DEFAULT_PASSWORD', 'defaultpass123')

        # Validate required environment variables
        if salon_name == 'Default Salon' or owner_email == 'owner@example.com':
            self.stdout.write(
                self.style.WARNING(
                    'Using default values. Set SEED_* environment variables for custom data.'
                )
            )

        try:
            with transaction.atomic():
                # Create address for the salon
                address, created = Address.objects.get_or_create(
                    street=salon_street,
                    city=salon_city,
                    postal_code=salon_postal_code,
                    defaults={},
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created address: {address.street}, {address.city} {address.postal_code}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Address already exists: {address.street}, {address.city} {address.postal_code}'
                        )
                    )

                # Create salon
                salon, created = Salon.objects.get_or_create(
                    name=salon_name, defaults={'phone_number': salon_phone_number}
                )
                if created:
                    salon.addresses.add(address)
                    self.stdout.write(
                        self.style.SUCCESS(f'Created salon: {salon.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Salon already exists: {salon.name}')
                    )
                    # Ensure address is associated even if salon exists
                    if not salon.addresses.filter(id=address.id).exists():
                        salon.addresses.add(address)
                        self.stdout.write(
                            self.style.SUCCESS('Associated address with existing salon')
                        )

                # Create owner user
                user, created = ExtendedUser.objects.get_or_create(
                    email=owner_email,
                    defaults={
                        'first_name': owner_first_name,
                        'last_name': owner_last_name,
                        'full_name': owner_full_name,
                        'phone_number': owner_phone_number,
                        'is_superuser': True,
                        'is_owner': True,
                        'is_staff': True,
                    },
                )

                if created:
                    # Set a default password for the new user
                    user.set_password(owner_password)
                    user.save()
                    # Add user to salon
                    user.salons.add(salon)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created owner user: {user.full_name} ({user.email})'
                        )
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f'Default password set to: {owner_password} (Please change this!)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'User already exists: {user.email}')
                    )
                    # Add salon to user if not already associated
                    if not user.salons.filter(id=salon.pk).exists():
                        user.salons.add(salon)
                        self.stdout.write(
                            self.style.SUCCESS('Added salon to existing user')
                        )

                # Summary
                self.stdout.write(self.style.SUCCESS('\n=== Seeding Complete ==='))
                self.stdout.write(f'Salon: {salon.name}')
                self.stdout.write(f'Phone Number: {salon.phone_number}')
                self.stdout.write(
                    f'Address: {address.street}, {address.city} {address.postal_code}'
                )
                self.stdout.write(
                    f'Owner: {user.full_name} ({user.email}) ({user.phone_number})'
                )
                self.stdout.write(self.style.SUCCESS('========================\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during seeding: {e!s}'))
            raise
