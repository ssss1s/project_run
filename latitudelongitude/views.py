from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
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

        # Получаем все позиции в правильном порядке
        positions = Position.objects.filter(run=run).order_by('date_time')
        total_distance_m = Decimal('0.0')
        segment_speeds = []

        # Рассчитываем скорости для всех существующих сегментов
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]
            segment_m = Decimal(geodesic(
                (float(prev.latitude), float(prev.longitude)),
                (float(curr.latitude), float(curr.longitude))
            ).meters)
            time_diff = (curr.date_time - prev.date_time).total_seconds()

            if time_diff > 0:
                speed = segment_m / Decimal(str(time_diff))
                segment_speeds.append(float(speed))
                total_distance_m += segment_m

        # Рассчитываем скорость для нового сегмента
        new_segment_m = Decimal('0.0')
        new_segment_speed = Decimal('0.0')

        if positions.exists():
            last_position = positions.last()
            new_segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)
            time_diff = (date_time - last_position.date_time).total_seconds()

            if time_diff > 0:
                new_segment_speed = new_segment_m / Decimal(str(time_diff))
                segment_speeds.append(float(new_segment_speed))
                total_distance_m += new_segment_m

        # Рассчитываем кумулятивные средние скорости
        cumulative_speeds = []
        running_sum = Decimal('0.0')
        for i, speed in enumerate(segment_speeds, 1):
            running_sum += Decimal(str(speed))
            cumulative_speeds.append(float(round(running_sum / Decimal(str(i)), 2)))

        # Обновляем данные забега
        if positions.exists():
            first_position = positions.first()
            total_time_sec = (date_time - first_position.date_time).total_seconds()
        else:
            total_time_sec = 0

        # Сохраняем последнюю кумулятивную среднюю
        if cumulative_speeds:
            run.speed = cumulative_speeds[-1]
        else:
            run.speed = 0.0

        run.distance = float(round(total_distance_m / 1000, 3))
        run.run_time_seconds = float(total_time_sec)
        run.save()

        # Сохраняем новую позицию
        serializer.validated_data.update({
            'distance': float(round(total_distance_m / 1000, 3)),
            'speed': float(round(new_segment_speed, 2)) if positions.exists() else 0.0,
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)