from django.urls import path
from .views import SubscribeToCoachViewAPIView

urlpatterns = [
    path('api/subscribe_to_coach/<int:id>/', SubscribeToCoachViewAPIView, name='subscribe_to_coach'),
]