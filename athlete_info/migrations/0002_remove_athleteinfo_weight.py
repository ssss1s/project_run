# Generated by Django 5.2 on 2025-07-11 12:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('athlete_info', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='athleteinfo',
            name='weight',
        ),
    ]
