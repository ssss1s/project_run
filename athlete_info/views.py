from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import AthleteInfo, ChallengeAthlete
from .serializers import AthleteInfoSerializer, ChallengeAthleteSerializer
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

    def update(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            athlete_info, created = AthleteInfo.objects.get_or_create(
                Info=user,
                defaults={'weight': None, 'goals': None}
            )

            serializer = AthleteInfoSerializer(athlete_info, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = ChallengeAthlete.objects.all()
    serializer_class = ChallengeAthleteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['athlete']






