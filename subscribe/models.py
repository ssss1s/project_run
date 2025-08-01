from django.db import models
from django.contrib.auth.models import User

class Subscribe(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')

    class Meta:
        unique_together = ('coach', 'athlete')