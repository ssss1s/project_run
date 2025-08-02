from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from .models import User, Subscribe


class SubscribeToCoachView(APIView):
     def post(self, request, coach_id):
        # 1. Проверяем существование пользователя с указанным coach_id
        try:
            user = User.objects.get(id=coach_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Проверяем, что пользователь является тренером
        if not user.is_staff:
            return Response(
                {'error': 'Указанный пользователь не является тренером'},
                status=status.HTTP_400_BAD_REQUEST
            )

        coach = user

        # 3. Проверяем наличие athlete в запросе
        athlete_id = request.data.get('athlete')
        if not athlete_id:
            return Response(
                {'error': 'Не указан ID атлета'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Проверяем существование атлета
        try:
            athlete = User.objects.get(id=athlete_id, is_staff=False)
        except User.DoesNotExist:
            return Response(
                {'error': 'Атлет не найден или не является атлетом'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5. Проверяем существующую подписку
        if Subscribe.objects.filter(coach=coach, athlete=athlete).exists():
            return Response(
                {'error': 'Подписка уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. Создаем подписку
        try:
            Subscribe.objects.create(coach=coach, athlete=athlete)
            return Response(
                {'success': 'Подписка успешно оформлена'},
                status=status.HTTP_200_OK
            )
        except IntegrityError:
            return Response(
                {'error': 'Ошибка создания подписки'},
                status=status.HTTP_400_BAD_REQUEST
            )