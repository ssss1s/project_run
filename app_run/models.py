from django.db import models
from django.contrib.auth.models import User



class RunStatus(models.TextChoices):
    INIT = 'init'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class Run(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    athlete = models.ForeignKey(User, related_name='runs', on_delete=models.CASCADE)
    status = models.CharField(max_length=12, choices=RunStatus.choices, default=RunStatus.INIT)
    distance = models.FloatField(default=0.0)
    run_time_seconds=models.FloatField(default=0.0)
    speed=models.FloatField(default=0.0)




