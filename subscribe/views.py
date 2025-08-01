
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from django.db import IntegrityError
from .models import User, Subscribe
class SubscribeToCoachViewAPIView(APIView):
    def post(self, request, coach_id):
        try:
            # 1. Проверка существования тренера
            coach = get_object_or_404(User, id=coach_id)

            if not coach.is_staff:
                return Response(
                    {'error': 'Указанный пользователь не является тренером'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Проверка наличия athlete в запросе
            athlete_id = request.data.get('athlete')
            if not athlete_id:
                return Response(
                    {'error': 'Не указан ID атлета'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. Проверка существования и типа атлета
            athlete = get_object_or_404(User, id=athlete_id)

            if athlete.is_staff:
                return Response(
                    {'error': 'Указанный пользователь не является атлетом'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Проверка существующей подписки
            if Subscribe.objects.filter(coach=coach, athlete=athlete).exists():
                return Response(
                    {'error': 'Подписка уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5. Создание подписки
            try:
                subscription = Subscribe.objects.create(coach=coach, athlete=athlete)
                return Response(
                    {
                        'success': 'Подписка успешно создана',
                        'subscription_id': subscription.id
                    },
                    status=status.HTTP_201_CREATED
                )
            except IntegrityError:
                return Response(
                    {'error': 'Ошибка создания подписки'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {'error': f'Произошла ошибка: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
