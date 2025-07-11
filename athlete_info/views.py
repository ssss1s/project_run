from rest_framework.viewsets import ModelViewSet
from .models import AthleteInfo
from .serializers import AthleteInfoSerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404



class AthleteViewSet(ModelViewSet):
    queryset = AthleteInfo.objects.select_related()
    serializer_class = AthleteInfoSerializer

    def get_object(self):
        user_id = self.kwargs.get('pk')
        user = get_object_or_404(User, pk=user_id)
        athlete_info, created = AthleteInfo.objects.get_or_create(
            Info=user,
            defaults={'weight': None, 'goals': None}  # Указываем дефолтные значения
        )
        return athlete_info


