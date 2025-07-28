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

        positions = Position.objects.filter(run=run).order_by('date_time')
        total_distance_m = Decimal('0.0')
        segment_speeds = []

        # Рассчитываем скорости существующих сегментов
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]
            segment_m = Decimal(geodesic(
                (float(prev.latitude), float(prev.longitude)),
                (float(curr.latitude), float(curr.longitude))
            ).meters)
            time_diff = Decimal(str((curr.date_time - prev.date_time).total_seconds()))

            if time_diff > 0:
                speed = segment_m / time_diff
                segment_speeds.append(float(speed))
                total_distance_m += segment_m

        # Рассчитываем новый сегмент
        new_segment_m = Decimal('0.0')
        new_segment_speed = Decimal('0.0')

        if positions.exists():
            last_position = positions.last()
            new_segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)
            time_diff = Decimal(str((date_time - last_position.date_time).total_seconds()))

            if time_diff > 0:
                new_segment_speed = new_segment_m / time_diff
                segment_speeds.append(float(new_segment_speed))
                total_distance_m += new_segment_m

        # Рассчитываем среднюю скорость
        if positions.exists():
            first_position = positions.first()
            total_time_sec = Decimal(str((date_time - first_position.date_time).total_seconds()))
            average_speed = total_distance_m / total_time_sec if total_time_sec > 0 else Decimal('0.0')
        else:
            average_speed = Decimal('0.0')
            total_time_sec = Decimal('0.0')

        # Обновляем данные забега
        run.speed = float(round(average_speed, 2))
        run.distance = float(round(total_distance_m / Decimal('1000'), 3))
        run.run_time_seconds = float(total_time_sec)
        run.save()

        # Сохраняем новую позицию
        serializer.validated_data.update({
            'distance': float(round(total_distance_m / Decimal('1000'), 3)),
            'speed': float(round(new_segment_speed, 2)) if positions.exists() else 0.0,
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)