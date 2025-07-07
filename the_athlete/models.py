from django.db import models

class Athlete(models.Model):
    username=models.CharField(max_length=100)
    last_name=models.CharField(max_length=100)
    first_name=models.CharField(max_length=100)


# В запросе на получение Забегов /api/runs/ добавь поле athlete_data, с сериализованным объектом Атлета, с полями id, username, last_name, first_name
# Избавься от проблемы n+1.
