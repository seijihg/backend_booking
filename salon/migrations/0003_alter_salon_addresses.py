# Generated by Django 4.1.4 on 2023-06-06 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("address", "0003_alter_address_postal_code"),
        ("salon", "0002_salon_created_salon_modified"),
    ]

    operations = [
        migrations.AlterField(
            model_name="salon",
            name="addresses",
            field=models.ManyToManyField(blank=True, to="address.address"),
        ),
    ]