from django.utils import timezone
from django.db import models
from app_run.models import Run


class Position(models.Model):
    run=models.ForeignKey(Run, on_delete=models.CASCADE)
    latitude=models.DecimalField(max_digits=9, decimal_places=4)
    longitude=models.DecimalField(max_digits=9, decimal_places=4)
    date_time = models.DateTimeField(default=timezone.now)
    distance = models.FloatField(default=0.0)
    speed = models.FloatField(default=0.0)


    class Meta:
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return f"Position for Run {self.run_id}"

