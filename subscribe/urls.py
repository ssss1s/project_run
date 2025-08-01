from django.urls import path
from .views import SubscribeViewSet

urlpatterns = [
    path('api/subscribe_to_coach/<int:id>/', SubscribeViewSet, name='subscribe-to-coach'),
]