from django.urls import path
from .views import AthleteViewSet

urlpatterns = [
    path('api/athlete_info/<int:user_id>/', AthleteViewSet.as_view({'get': 'list','put': 'update'}), name='athlete_info'),
]