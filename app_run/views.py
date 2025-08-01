from decimal import Decimal
from django.db.models import Min, Max
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from geopy.distance import geodesic
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import viewsets, status
from athlete_info.models import ChallengeAthlete
from item.models import CollectibleItem
from latitudelongitude.models import Position
from .models import Run, RunStatus
from .serializers import UserSerializer, UserDetailSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import RunSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q

class UserPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'size'
    max_page_size = 50
    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get(self.page_size_query_param):
            return super().paginate_queryset(queryset, request, view)
        return None

class RunPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'size'
    max_page_size = 50
    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get(self.page_size_query_param):
            return super().paginate_queryset(queryset, request, view)
        return None

class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related()
    serializer_class = RunSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'athlete']
    ordering_fields =['created_at']
    pagination_class = RunPagination

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['last_name', 'first_name']
    ordering_fields = ['date_joined']
    pagination_class = UserPagination

    def get_queryset(self):
        queryset = User.objects.filter(is_superuser=False).annotate(
            runs_finished_count=Count(
                'runs',
                filter=Q(runs__status=RunStatus.FINISHED),
                distinct=True
            )
        )

        user_type = self.request.query_params.get('type')
        if user_type == 'coach':
            queryset = queryset.filter(is_staff=True)
        elif user_type == 'athlete':
            queryset = queryset.filter(is_staff=False)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return UserSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = User.objects.filter(is_superuser=False).annotate(
            runs_finished_count=Count(
                'runs',
                filter=Q(runs__status=RunStatus.FINISHED),
                distinct=True
            )
        )

        user_type = self.request.query_params.get('type')
        if user_type == 'coach':
            queryset = queryset.filter(is_staff=True)
        elif user_type == 'athlete':
            queryset = queryset.filter(is_staff=False)

        return queryset


    def get_serializer_class(self):
        if self.action == 'list':
            return UserSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return super().get_serializer_class()


class RunStartAPIView(APIView):
    def post(self, request, run_id):
        run = get_object_or_404(Run, pk=run_id)

        if run.status != RunStatus.INIT:
            return Response(
                {"error": "Запуск может быть начат только со статуса init"},
                status=status.HTTP_400_BAD_REQUEST
            )

        run.status = RunStatus.IN_PROGRESS
        run.save()
        return Response(
            {"status": "Запуск начался успешно"},
            status=status.HTTP_200_OK
        )


class RunStopAPIView(APIView):
    def post(self, request, run_id):
        with transaction.atomic():
            run = get_object_or_404(Run.objects.select_for_update(), pk=run_id)

            if run.status != RunStatus.IN_PROGRESS:
                return Response(
                    {"error": "Запуск может быть остановлен только из состояния in_progress"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            extreme_positions = Position.objects.filter(run=run).aggregate(
                first_position=Min('date_time'),
                last_position=Max('date_time')
            )

            run_time_seconds = 0.0
            if extreme_positions['first_position'] and extreme_positions['last_position']:
                run_time_seconds = (extreme_positions['last_position'] -
                                  extreme_positions['first_position']).total_seconds()


            # Получаем все точки маршрута
            positions = Position.objects.filter(run=run).order_by('id')
            total_distance_meters = 0.0
            collected_items = set()

            if positions.count() > 1:
                for i in range(1, positions.count()):
                    prev_pos = positions[i - 1]
                    curr_pos = positions[i]

                    # Проверяем координаты
                    if None in (prev_pos.latitude, prev_pos.longitude, curr_pos.latitude, curr_pos.longitude):
                        continue

                    # Рассчитываем расстояние между точками
                    segment_distance = geodesic(
                        (prev_pos.latitude, prev_pos.longitude),
                        (curr_pos.latitude, curr_pos.longitude)
                    ).meters
                    total_distance_meters += segment_distance

                    # Поиск ближайших артефактов
                    current_point = (curr_pos.latitude, curr_pos.longitude)

                    # Оптимизированный поиск в радиусе ~100 метров
                    lat_range = (
                        curr_pos.latitude - Decimal('0.0009'),
                        curr_pos.latitude + Decimal('0.0009')
                    )
                    lon_range = (
                        curr_pos.longitude - Decimal('0.0009'),
                        curr_pos.longitude + Decimal('0.0009')
                    )

                    nearby_items = CollectibleItem.objects.filter(
                        latitude__range=lat_range,
                        longitude__range=lon_range
                    ).exclude(items=run.athlete)  # Используем правильный related_name

                    for item in nearby_items:
                        item_point = (item.latitude, item.longitude)
                        distance_to_item = geodesic(current_point, item_point).meters

                        if distance_to_item <= 100:
                            item.items.add(run.athlete)
                            collected_items.add(item.id)


            total_distance_km = round(total_distance_meters / 1000, 2)
            run_speed=round((total_distance_meters /run_time_seconds), 2)




            # Обновляем забег
            run.status = RunStatus.FINISHED
            run.run_time_seconds = run_time_seconds
            run.save()

            try:
                self.check_achievements(run.athlete, len(collected_items))
            except Exception as e:
                print(f"Error in check_achievements: {str(e)}")
                raise  # повторно поднимаем исключение


            return Response({
                "status": "Запуск успешно остановлен",
                "distance": total_distance_km,
                "points_count": positions.count(),
                "collected_items_count": len(collected_items)
            }, status=status.HTTP_200_OK)

    def check_achievements(self, athlete, new_items_count):
        """Проверка и выдача достижений"""
        # Проверяем количество завершенных забегов
        finished_runs = Run.objects.filter(
            athlete=athlete,
            status=RunStatus.FINISHED
        )
        finished_runs_count = finished_runs.count()

        # Проверяем сумму дистанций
        runs_distance_sum = sum(
            r.distance for r in finished_runs
            if r.distance is not None
        )

        # Награда за 10 забегов
        if finished_runs_count == 10 and not ChallengeAthlete.objects.filter(
                athlete=athlete,
                full_name="Сделай 10 Забегов!"
        ).exists():
            ChallengeAthlete.objects.create(
                athlete=athlete,
                full_name="Сделай 10 Забегов!"
            )

        # Награда за 50 км
        if runs_distance_sum >= 50 and not ChallengeAthlete.objects.filter(
                athlete=athlete,
                full_name="Пробеги 50 километров!"
        ).exists():
            ChallengeAthlete.objects.create(
                athlete=athlete,
                full_name="Пробеги 50 километров!"
            )

        fast_runs = finished_runs.filter(
            distance__gte=2.0,  # 2 км или больше
            run_time_seconds__lte=600  # 10 минут или меньше (600 секунд)
        )
        if fast_runs.exists() and not ChallengeAthlete.objects.filter(
                athlete=athlete,
                full_name="2 километра за 10 минут!"
        ).exists():
            ChallengeAthlete.objects.create(
                athlete=athlete,
                full_name="2 километра за 10 минут!"
            )

@api_view(['GET'])
def company_info(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)






