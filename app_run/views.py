from decimal import Decimal
from django.db.models import Min, Max
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from geopy.distance import geodesic
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
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
            # Получаем позиции, сортированные по времени
            positions = Position.objects.filter(run=run).order_by('date_time')

            # Инициализация
            total_distance_m = Decimal('0.0')
            collected_items = set()

            # Расчет общего расстояния
            if positions.count() > 1:
                prev_pos = positions[0]
                for curr_pos in positions[1:]:
                    if None in (prev_pos.latitude, prev_pos.longitude,
                                curr_pos.latitude, curr_pos.longitude):
                        continue

                    segment_m = Decimal(str(geodesic(
                        (float(prev_pos.latitude), float(prev_pos.longitude)),
                        (float(curr_pos.latitude), float(curr_pos.longitude))
                    ).meters))

                    total_distance_m += segment_m
                    prev_pos = curr_pos

            # Расчет общего времени
            if positions.count() > 1:
                total_time_s = Decimal(str(
                    (positions.last().date_time - positions.first().date_time).total_seconds()
                ))
            else:
                total_time_s = Decimal('0.0')

            # Расчет средней скорости
            avg_speed_m_s = (total_distance_m / total_time_s).quantize(Decimal('0.00')) \
                if total_time_s > Decimal('0') else Decimal('0.00')

            # Обновление забега
            run.status = RunStatus.FINISHED
            run.distance = (total_distance_m / Decimal('1000')).quantize(Decimal('0.00'))
            run.speed = avg_speed_m_s
            run.run_time_seconds = total_time_s.quantize(Decimal('0.00'))
            run.save()

            return Response({
                "status": "Запуск успешно остановлен",
                "distance": float(run.distance),
                "avg_speed_m_s": float(avg_speed_m_s),
                "run_time_seconds": float(run.run_time_seconds)
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





@api_view(['GET'])
def company_info(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)






