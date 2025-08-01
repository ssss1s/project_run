from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from subscribe.models import Subscribe
from subscribe.serializers import SubscribeSerializer


class SubscribeToCoachViewAPIView(APIView):
    def get(self, request, coach_id=None):
        """
        GET /api/subscribe_to_coach/ - список всех подписок
        GET /api/subscribe_to_coach/97/ - подписки конкретного тренера
        """
        if coach_id:
            # Получаем подписки конкретного тренера
            coach = get_object_or_404(User, id=coach_id, is_staff=True)
            subscriptions = Subscribe.objects.filter(coach=coach)
        else:
            # Все подписки (можно добавить пагинацию)
            subscriptions = Subscribe.objects.all()

        serializer = SubscribeSerializer(subscriptions, many=True)
        return Response(serializer.data)
    def post(self, request, coach_id):
        coach = get_object_or_404(User, id=coach_id)

        if not coach.is_staff:
            return Response(
                {'error': 'The user is not a coach'},
                status=status.HTTP_400_BAD_REQUEST
            )

        athlete_id = request.data.get('athlete')
        if not athlete_id:
            return Response(
                {'error': 'Athlete ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            athlete = User.objects.get(id=athlete_id, is_staff=False)
        except User.DoesNotExist:
            return Response(
                {'error': 'Athlete not found or is not an athlete'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscribe.objects.filter(coach=coach, athlete=athlete).exists():
            return Response(
                {'error': 'Already subscribed to this coach'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscribe.objects.create(coach=coach, athlete=athlete)
        return Response(
            {'success': 'Subscribed successfully'},
            status=status.HTTP_200_OK
        )

