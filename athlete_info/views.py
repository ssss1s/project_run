from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, viewsets
from .models import AthleteInfo, ChallengeAthlete
from .serializers import AthleteInfoSerializer, ChallengeAthleteSerializer, \
    ChallengeSummarySerializer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import generics
from collections import defaultdict


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

class ChallengesSummaryView(generics.ListAPIView):
    serializer_class = ChallengeSummarySerializer

    def get_queryset(self):
        # ЕДИНСТВЕННЫЙ запрос с явным указанием нужных полей
        queryset = ChallengeAthlete.objects.select_related('athlete').only(
            'full_name',
            'athlete__id',
            'athlete__username',
            'athlete__first_name',
            'athlete__last_name'
        ).order_by('full_name')

        # Кэшируем результаты запроса
        challenges = list(queryset)

        # Группируем вручную
        grouped = defaultdict(list)
        for challenge in challenges:
            grouped[challenge.full_name].append(challenge.athlete)

        return [{'full_name': k, 'athletes': v} for k, v in grouped.items()]







