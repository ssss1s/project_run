from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.response import Response
from subscribe.models import Subscribe
from coach_rating.models import CoachRating


class RateCoachView(APIView):
    def post(self, request, coach_id):
        coach = get_object_or_404(User, id=coach_id, is_staff=True)
        athlete_id = request.data.get('athlete')

        if not athlete_id:
            return Response({'error': 'Не указан ID атлета'}, status=400)

        athlete = get_object_or_404(User, id=athlete_id, is_staff=False)
        subscription = get_object_or_404(Subscribe, coach=coach, athlete=athlete)

        rating = request.data.get('rating')
        if rating is None or not 1 <= int(rating) <= 5:
            return Response({'error': 'Рейтинг должен быть от 1 до 5'}, status=400)

        CoachRating.objects.update_or_create(
            subscription=subscription,
            defaults={'rating': rating}
        )
        return Response({'success': 'Рейтинг обновлён'}, status=200)