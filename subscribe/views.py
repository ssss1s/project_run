from rest_framework import viewsets
from subscribe.models import Subscribe
from subscribe.serializers import SubscribeSerializer


class SubscribeViewSet(viewsets.ModelViewSet):
    queryset = Subscribe.objects.all()
    serializer_class = SubscribeSerializer
