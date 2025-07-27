from django.utils import timezone
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response

from app_run.models import Run
from .models import Position
from .serializers import PositionSerializer
from geopy.distance import geodesic

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['run']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        run = serializer.validated_data['run']
        latitude = Decimal(str(serializer.validated_data['latitude']))
        longitude = Decimal(str(serializer.validated_data['longitude']))
        date_time = serializer.validated_data.get('date_time', timezone.now())

        previous_positions = Position.objects.filter(run=run).order_by('date_time')
        distance_m = Decimal('0.0')  # Накопленное расстояние в метрах
        speed = Decimal('0.0')  # Скорость в м/с

        if previous_positions.exists():
            last_position = previous_positions.last()

            # Расстояние между точками в метрах
            segment_m = Decimal(str(geodesic(
                (Decimal(last_position.latitude), Decimal(last_position.longitude)),
                (Decimal(latitude), Decimal(longitude))
            ).meters))

            time_diff = (date_time - last_position.date_time).total_seconds()

            if time_diff > 0:
                # Скорость = расстояние (км) * 1000 / время (с) → результат в м/с
                speed = (segment_m * Decimal('1000')) / Decimal(str(time_diff))

            # Накопленное расстояние в километрах (без деления на 1000!)
            distance_m = Decimal(str(last_position.distance)) + segment_m

        # Округляем до сотых
        distance_m = round(distance_m / 1000, 2)
        speed = round(speed, 2)

        serializer.validated_data.update({
            'distance': float(distance_m),  # Сохраняем в километрах
            'speed': float(speed),
            'date_time': date_time
        })

        self.perform_create(serializer)
        self.update_run_average_speed(run.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update_run_average_speed(self, run_id):
        # Получаем все позиции забега в хронологическом порядке
        positions = Position.objects.filter(run_id=run_id).order_by('date_time')

        # Если позиций меньше 2, среднюю скорость считать нельзя
        if positions.count() < 2:
            Run.objects.filter(id=run_id).update(speed=0.0)
            return

        total_distance_m = 0.0  # Общее расстояние в метрах
        total_time_s = 0.0  # Общее время в секундах

        # Проходим по всем парам последовательных позиций
        for i in range(1, len(positions)):
            prev_pos = positions[i - 1]
            curr_pos = positions[i]

            # Рассчитываем расстояние между позициями в метрах
            distance_m = geodesic(
                (prev_pos.latitude, prev_pos.longitude),
                (curr_pos.latitude, curr_pos.longitude)
            ).meters

            # Рассчитываем временной интервал в секундах
            time_s = (curr_pos.date_time - prev_pos.date_time).total_seconds()

            # Суммируем общие показатели
            total_distance_m += distance_m
            total_time_s += time_s

        # Рассчитываем среднюю скорость (м/с)
        if total_time_s > 0:
            avg_speed_ms = total_distance_m / total_time_s
            # Округляем до двух знаков после запятой
            avg_speed_ms = round(avg_speed_ms, 2)
        else:
            avg_speed_ms = 0.0

        # Обновляем запись забега
        Run.objects.filter(id=run_id).update(speed=avg_speed_ms)
