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

        # Получаем все позиции в хронологическом порядке
        positions = Position.objects.filter(run=run).order_by('date_time')
        segment_speeds = []
        total_distance_m = Decimal('0.0')

        # Рассчитываем скорости для всех существующих сегментов
        prev_position = None
        for position in positions:
            if prev_position:
                segment_m = Decimal(geodesic(
                    (float(prev_position.latitude), float(prev_position.longitude)),
                    (float(position.latitude), float(position.longitude))
                ).meters)
                time_diff = (position.date_time - prev_position.date_time).total_seconds()

                if time_diff > 0:
                    speed = segment_m / Decimal(str(time_diff))
                    segment_speeds.append(float(speed))
                    total_distance_m += segment_m
            prev_position = position

        # Рассчитываем скорость для нового сегмента
        if positions.exists():
            last_position = positions.last()
            segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)
            time_diff = (date_time - last_position.date_time).total_seconds()

            if time_diff > 0:
                segment_speed = segment_m / Decimal(str(time_diff))
                segment_speeds.append(float(segment_speed))
                total_distance_m += segment_m
        else:
            segment_speed = Decimal('0.0')

        # Рассчитываем среднюю скорость
        if segment_speeds:
            average_speed = Decimal(sum(segment_speeds)) / Decimal(len(segment_speeds))
        else:
            average_speed = Decimal('0.0')

        # Обновляем данные забега
        if positions.exists():
            total_time_sec = (date_time - positions.first().date_time).total_seconds()
        else:
            total_time_sec = 0

        run.speed = float(round(average_speed, 2))
        run.distance = float(round(total_distance_m / 1000, 3))
        run.run_time_seconds = float(total_time_sec)
        run.save()

        # Сохраняем новую позицию
        serializer.validated_data.update({
            'distance': float(round(total_distance_m / 1000, 3)),
            'speed': float(round(segment_speed, 2)) if positions.exists() else 0.0,
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)