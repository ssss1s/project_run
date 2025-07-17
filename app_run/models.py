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
    distance = models.DecimalField(max_digits=6, decimal_places=2, default=0)






    #Создай два API endpoint: /api/runs/{run_id}/start/ и /api/runs/{run_id}/stop/  .
    #У модели Run добавь новое поле  status  с тремя возможными значениями: 'init', 'in_progress' и 'finished'.
    #При создании объекта класса Run, status равен 'init'.
    #Когда забег запускают (API запрос на /api/runs/{run_id}/start/) , status равен 'in_progress' .
    #Когда забег завершают (API запрос на /api/runs/{run_id}/stop/), status равен  'finished'.
    #HTTP ответ должен быть в формате JSON
    #Проверки:

    #когда пытаются отправить запрос с несуществующим id - нужно вернуть статус-код 404
    #когда пытаются стартовать забег который уже стартовал или закончен - нужно вернуть статус-код 400
    #когда пытаются завершить забег, который еще не запущен - нужно вернуть статус-код 400
