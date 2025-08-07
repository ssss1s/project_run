from django.contrib.auth.models import User
from rest_framework import status
from app_run.models import Run
from coach_rating.models import CoachRating
from subscribe.models import Subscribe
from django.db.models import Sum, Avg
from rest_framework.views import APIView
from rest_framework.response import Response



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


class AnalyticsForCoachView(APIView):
    def get(self, request, coach_id):
        # 1. Получаем ID атлетов тренера
        athlete_ids = Subscribe.objects.filter(
            coach_id=coach_id
        ).values_list('athlete_id', flat=True).distinct()

        if not athlete_ids:
            return Response({"error": "У тренера нет атлетов"}, status=404)

        # 2. Самый длинный забег
        longest_run = Run.objects.filter(
            athlete_id__in=athlete_ids,
            status='finished'
        ).order_by('-distance').values('athlete_id', 'distance').first()

        # 3. Суммарный пробег (в км)
        total_runs = Run.objects.filter(
            athlete_id__in=athlete_ids,
            status='finished'
        ).values('athlete_id').annotate(
            total_distance=Sum('distance')
        ).order_by('-total_distance').first()

        # 4. Средняя скорость (в м/с, БЕЗ конвертации)
        avg_speed = Run.objects.filter(
            athlete_id__in=athlete_ids,
            status='finished'
        ).values('athlete_id').annotate(
            avg_speed=Avg('speed')  # Оставляем в м/с
        ).order_by('-avg_speed').first()

        response_data = {
            'longest_run_user': longest_run['athlete_id'] if longest_run else None,
            'longest_run_value': round(float(longest_run['distance']), 2) if longest_run else 0,
            'total_run_user': total_runs['athlete_id'] if total_runs else None,
            'total_run_value': round(float(total_runs['total_distance']), 2) if total_runs else 0,
            'speed_avg_user': avg_speed['athlete_id'] if avg_speed else None,
            'speed_avg_value': round(float(avg_speed['avg_speed']), 2) if avg_speed else 0,
        }

        return Response(response_data)