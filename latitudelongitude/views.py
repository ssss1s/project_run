from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Position
from .serializers import PositionSerializer
from geopy.distance import geodesic
from app_run.models import Run
from django.utils import timezone


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['run']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Получаем данные из запроса
        run_id = serializer.validated_data['run'].id
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        date_time = serializer.validated_data.get('date_time', timezone.now())

        # Получаем предыдущие позиции для этого забега
        previous_positions = Position.objects.filter(run_id=run_id).order_by('date_time')

        distance = 0.0
        speed = 0.0

        if previous_positions.exists():
            last_position = previous_positions.last()

            # Вычисляем расстояние между точками в метрах
            current_coords = (float(latitude), float(longitude))
            last_coords = (float(last_position.latitude), float(last_position.longitude))
            segment_distance = geodesic(last_coords, current_coords).meters

            # Вычисляем разницу во времени в секундах
            time_diff = (date_time - last_position.date_time).total_seconds()

            # Рассчитываем скорость (м/с)
            if time_diff > 0:
                speed = round(segment_distance / time_diff, 2)

            # Общее расстояние
            distance = round(last_position.distance + segment_distance, 2)

        # Добавляем вычисленные значения в данные перед сохранением
        serializer.validated_data['distance'] = distance
        serializer.validated_data['speed'] = speed
        serializer.validated_data['date_time'] = date_time

        # Сохраняем позицию
        self.perform_create(serializer)
        position = serializer.instance

        # Обновляем среднюю скорость забега, если это последняя позиция
        if not Position.objects.filter(run_id=run_id, date_time__gt=date_time).exists():
            self.update_run_average_speed(run_id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update_run_average_speed(self, run_id):
        """Обновляет среднюю скорость для забега"""
        positions = Position.objects.filter(run_id=run_id).exclude(speed=0.0)

        if positions.exists():
            average_speed = round(sum(p.speed for p in positions) / positions.count(), 2)
            Run.objects.filter(id=run_id).update(speed=average_speed)