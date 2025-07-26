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
        distance = Decimal('0.0')  # Накопленное расстояние в километрах
        speed = Decimal('0.0')  # Скорость в м/с

        if previous_positions.exists():
            last_position = previous_positions.last()

            # Расстояние между точками в километрах
            segment_km = Decimal(str(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).kilometers))  # Используем .kilometers вместо .meters

            time_diff = (date_time - last_position.date_time).total_seconds()

            if time_diff > 0:
                # Скорость = расстояние (км) * 1000 / время (с) → результат в м/с
                speed = (segment_km * Decimal('1000')) / Decimal(str(time_diff))

            # Накопленное расстояние в километрах
            distance = Decimal(str(last_position.distance)) + segment_km

        # Округляем до сотых
        distance = round(distance, 2)
        speed = round(speed, 2)

        serializer.validated_data.update({
            'distance': float(distance),
            'speed': float(speed),
            'date_time': date_time
        })

        self.perform_create(serializer)
        self.update_run_average_speed(run.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update_run_average_speed(self, run_id):
        positions = Position.objects.filter(run_id=run_id).order_by('date_time')
        if positions.count() < 2:
            return  # Недостаточно данных для расчета

        total_distance = Decimal('0.0')  # в километрах
        total_time = Decimal('0.0')  # в часах

        prev_position = positions.first()

        for current_position in positions[1:]:
            # Рассчитываем расстояние между точками
            segment_distance = Decimal(str(geodesic(
                (float(prev_position.latitude), float(prev_position.longitude)),
                (float(current_position.latitude), float(current_position.longitude))
            ).kilometers))

            # Рассчитываем время между точками в часах
            time_diff = (current_position.date_time - prev_position.date_time).total_seconds()
            segment_time = Decimal(str(time_diff)) / Decimal('3600')  # секунды -> часы

            total_distance += segment_distance
            total_time += segment_time
            prev_position = current_position

            if total_time > 0:
            # Средняя скорость = общее расстояние / общее время
                avg_speed = total_distance / total_time  # результат в км/ч
            # Конвертируем в м/с (если нужно)
            avg_speed_m_s = avg_speed * Decimal('1000') / Decimal('3600')  # км/ч -> м/с
            Run.objects.filter(id=run_id).update(speed=round(float(avg_speed_m_s), 2))