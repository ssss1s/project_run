from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status
from subscribe.models import Subscribe
from coach_rating.models import CoachRating


class RateCoachView(APIView):
    def post(self, request, coach_id):
        """
        Установка рейтинга тренера
        - Тренер должен существовать и быть is_staff=True
        - Атлет должен существовать и быть is_staff=False
        - Атлет должен быть подписан на тренера
        - Рейтинг должен быть целым числом 1-5
        """
        # Проверка тренера
        try:
            coach = User.objects.get(id=coach_id, is_staff=True)
        except User.DoesNotExist:
            return Response(
                {'error': 'Тренер не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверка athlete_id в запросе
        athlete_id = request.data.get('athlete')
        if not athlete_id:
            return Response(
                {'error': 'Поле athlete обязательно'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка существования атлета
        try:
            athlete = User.objects.get(id=athlete_id, is_staff=False)
        except User.DoesNotExist:
            return Response(
                {'error': 'Атлет не найден'},
                status=status.HTTP_400_BAD_REQUEST  # Важно: возвращаем 400, а не 404
            )

        # Проверка подписки
        if not Subscribe.objects.filter(coach=coach, athlete=athlete).exists():
            return Response(
                {'error': 'Атлет не подписан на тренера'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Валидация рейтинга
        rating = request.data.get('rating')
        if rating is None:
            return Response(
                {'error': 'Поле rating обязательно'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Рейтинг должен быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not 1 <= rating <= 5:
            return Response(
                {'error': 'Рейтинг должен быть от 1 до 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Сохранение рейтинга
        subscription = Subscribe.objects.get(coach=coach, athlete=athlete)
        CoachRating.objects.update_or_create(
            subscription=subscription,
            defaults={'rating': rating}
        )

        return Response(
            {'success': 'Рейтинг успешно сохранен'},
            status=status.HTTP_200_OK
        )