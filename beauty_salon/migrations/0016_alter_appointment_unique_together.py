# Generated by Django 5.2 on 2025-04-21 06:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("beauty_salon", "0015_alter_appointment_unique_together"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="appointment",
            unique_together=set(),
        ),
    ]
