from django.urls import path
from .views import AthleteViewSet, ChallengeViewSet, ChallengesSummaryView

urlpatterns = [
    path('api/athlete_info/<int:user_id>/', AthleteViewSet.as_view({'get': 'list','put': 'update'}), name='athlete_info'),
    path('api/challenges/', ChallengeViewSet.as_view(), name='challenge-list'),
    path('api/challenges_summary/', ChallengesSummaryView.as_view(), name='challenges-summary'),

]