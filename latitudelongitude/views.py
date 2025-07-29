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
        current_lat = Decimal(str(serializer.validated_data['latitude']))
        current_lon = Decimal(str(serializer.validated_data['longitude']))
        current_time = serializer.validated_data.get('date_time', timezone.now())

        # Получаем все существующие позиции
        existing_positions = Position.objects.filter(run=run).order_by('date_time')

        # Создаем список словарей для единообразия
        positions_list = [
            {
                'latitude': pos.latitude,
                'longitude': pos.longitude,
                'date_time': pos.date_time
            }
            for pos in existing_positions
        ]

        # Добавляем новую позицию
        positions_list.append({
            'latitude': current_lat,
            'longitude': current_lon,
            'date_time': current_time
        })

        # Сортируем по времени
        positions_list.sort(key=lambda x: x['date_time'])

        # Пересчитываем все показатели
        total_distance = Decimal('0')
        total_time = Decimal('0')
        segments = []

        for i in range(1, len(positions_list)):
            prev = positions_list[i - 1]
            curr = positions_list[i]

            # Рассчитываем временной интервал
            time_diff = (curr['date_time'] - prev['date_time']).total_seconds()
            if time_diff <= 0:
                continue

            # Рассчитываем расстояние
            distance = Decimal(geodesic(
                (float(prev['latitude']), float(prev['longitude'])),
                (float(curr['latitude']), float(curr['longitude']))
            ).meters)

            speed = distance / Decimal(str(time_diff)) if time_diff > 0 else Decimal('0')

            total_distance += distance
            total_time += Decimal(str(time_diff))
            segments.append({
                'distance': float(round(distance, 2)),
                'time': time_diff,
                'speed': speed
            })

        # Обновляем показатели забега
        run.distance = float(round(total_distance / Decimal('1000'), 5))
        run.run_time_seconds = float(round(total_time, 1))
        run.speed = float(round(
            (total_distance / total_time) if total_time > 0 else Decimal('0'),
            2
        ))
        run.save()

        # Данные для новой позиции
        current_speed = segments[-1]['speed'] if segments else Decimal('0')
        serializer.validated_data.update({
            'distance': run.distance,
            'speed': float(round(current_speed, 2)),
            'date_time': current_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)