### Developer

```
pip install pip-tools
pip-compile requirements.in
pip install -r requirements.txt
```

```
docker compose run --rm --service-ports web python manage.py runserver 0.0.0.0:8000
```

# Database Seeding

This project includes a management command to seed the database with initial data.

## Setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to customize the seed data values:
   ```env
   # Seed data (used by management command)
   SEED_SALON_NAME=USA Nails Berkhamsted
   SEED_SALON_STREET=175 High St
   SEED_SALON_CITY=Berkhamsted
   SEED_SALON_POSTAL_CODE=HP4 3AP
   SEED_OWNER_EMAIL=seiji@o2.pl
   SEED_OWNER_FIRST_NAME=Le
   SEED_OWNER_LAST_NAME=Hoang Ngo
   SEED_OWNER_FULL_NAME=Le Hoang Ngo
   SEED_OWNER_DEFAULT_PASSWORD=
   ```

## Running the Seed Command

To seed the database with the configured data:

```bash
docker compose run --rm web python manage.py seed_data
```

This command will:

- Create a salon with the specified name
- Create an address for the salon
- Create an owner user with the specified details
- Associate the owner with the salon
- Make the owner a staff member (can access Django admin)

## Security Notes

- The `.env` file is not committed to version control (it's in `.gitignore`)
- Always change the default password after seeding
- Keep sensitive seed data in environment variables, not in code
- Use strong passwords in production environments

## Default Values

If environment variables are not set, the command will use default values:

- Salon Name: "Default Salon"
- Address: "123 Default St, London SW1A 1AA"
- Owner Email: "owner@example.com"
- Owner Name: "Default Owner"
- Password: "defaultpass123"

The command will warn you if default values are being used.

## Idempotency

The seed command is idempotent - it can be run multiple times safely:

- It won't create duplicate records
- It uses `get_or_create` to check for existing data
- It will update associations if needed
