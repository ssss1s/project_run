from django.db import models
from django.contrib.auth.models import User

class AthleteInfo(models.Model):
    weight = models.IntegerField(null=True, blank=True)
    goals = models.CharField(max_length=1000, null=True, blank=True)
    Info = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_info')



class ChallengeAthlete(models.Model):
        full_name=models.CharField(max_length=100)
        athlete=models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges')


