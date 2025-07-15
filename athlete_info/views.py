from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, viewsets

from app_run.models import Run, RunStatus
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


from django.db import connection
from rest_framework import status
from rest_framework.response import Response


import logging
logger = logging.getLogger(__name__)

class StopRunView(APIView):
    def post(self, request, run_id):
        try:
            with transaction.atomic():
                # 1. Получаем забег
                run = Run.objects.get(pk=run_id)
                logger.info(f"Обрабатываем забег ID {run_id}. Текущий статус: {run.status}")

                # 2. Проверяем статус
                if run.status != 'finished':
                    logger.warning(f"Неверный статус забега: {run.status}")
                    return Response(...)

                # 3. Подсчёт завершённых забегов
                finished_runs = Run.objects.filter(
                    athlete_id=run.athlete_id,
                    status='finished'
                ).count()
                logger.info(f"Завершённых забегов: {finished_runs}")

                # 4. Создание достижения
                if finished_runs == 10:
                    logger.info("Условие выполнено (10 забегов). Пытаемся создать запись...")
                    try:
                        obj = ChallengeAthlete.objects.create(
                            athlete_id=run.athlete_id,
                            full_name="Сделай 10 Забегов!"
                        )
                        logger.info(f"Запись создана! ID: {obj.id}")
                    except Exception as e:
                        logger.error(f"Ошибка создания: {str(e)}")
                        raise

                return Response(...)

        except Exception as e:
            logger.error(f"Ошибка в обработке: {str(e)}")
            return Response(...)








