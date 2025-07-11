from django.db import models
from django.contrib.auth.models import User

class AthleteInfo(models.Model):
    weight = models.FloatField(null=True, blank=True)  # Разрешаем NULL
    goals = models.CharField(max_length=10000, null=True, blank=True)  # Разрешаем NULL
    Info = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_info')



