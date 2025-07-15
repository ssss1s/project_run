from django.urls import path
from .views import AthleteViewSet, ChallengeViewSet

urlpatterns = [
    path('api/athlete_info/<int:user_id>/', AthleteViewSet.as_view({'get': 'list','put': 'update'}), name='athlete_info'),
    path('api/challenges/', ChallengeViewSet.as_view(), name='challenge-list'),
]