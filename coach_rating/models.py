from django.db import models
from subscribe.models import Subscribe

class CoachRating(models.Model):
    subscription = models.OneToOneField(
        Subscribe,
        on_delete=models.CASCADE,
        related_name='coach_rating',
    )
    rating = models.PositiveSmallIntegerField(null=True)  # null = оценка не выставлена

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__range=(1, 5)) | models.Q(rating__isnull=True),
                name='rating_between_1_and_5'
            )
        ]
        db_table = 'coachrating_coachrating'