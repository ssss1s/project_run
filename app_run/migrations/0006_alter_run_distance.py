# Generated by Django 5.2 on 2025-07-17 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_run', '0005_alter_run_distance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='distance',
            field=models.DecimalField(decimal_places=100, default=0, max_digits=100),
        ),
    ]
