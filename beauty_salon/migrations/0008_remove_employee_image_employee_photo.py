# Generated by Django 5.1.6 on 2025-02-21 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beauty_salon', '0007_employee_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='image',
        ),
        migrations.AddField(
            model_name='employee',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='employees/', verbose_name='Фотография'),
        ),
    ]
