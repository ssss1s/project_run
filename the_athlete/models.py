from django.contrib.auth.models import User
from django.db import models

class Athlete(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)


# В запросе на получение Забегов /api/runs/ добавь поле athlete_data, с сериализованным объектом Атлета, с полями id, username, last_name, first_name
# Избавься от проблемы n+1.
