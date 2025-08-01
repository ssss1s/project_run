from django.db import models
from django.contrib.auth.models import User


class CollectibleItem(models.Model):
    name = models.CharField(max_length=255)
    uid = models.CharField(max_length=100, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    picture = models.URLField()
    value = models.IntegerField()
    items = models.ManyToManyField(User, related_name='items')


    def __str__(self):
        return self.name