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

        # Получаем агрегированные данные по существующим позициям
        existing_data = Position.objects.filter(run=run).aggregate(
            total_speed=Sum('speed'),
            count=Count('id'),
            total_distance=Sum('distance')
        )

        # Рассчитываем новый сегмент
        new_segment_m = Decimal('0.0')
        new_segment_speed = Decimal('0.0')

        if existing_data['count'] > 0:
            last_position = Position.objects.filter(run=run).latest('date_time')
            new_segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

            time_diff = (date_time - last_position.date_time).total_seconds()
            if time_diff > 0:
                new_segment_speed = new_segment_m / Decimal(str(time_diff))

        # Рассчитываем новую среднюю скорость
        if existing_data['count'] > 0:
            total_speed = Decimal(str(existing_data['total_speed'])) + new_segment_speed
            total_count = existing_data['count'] + 1
            average_speed = total_speed / Decimal(str(total_count))

            # Обновляем общее расстояние
            total_distance_km = Decimal(str(existing_data['total_distance'])) + (new_segment_m / Decimal('1000'))
        else:
            average_speed = new_segment_speed
            total_distance_km = new_segment_m / Decimal('1000')
            total_count = 1 if new_segment_m > 0 else 0

        # Обновляем данные забега
        run.speed = float(round(average_speed, 2))
        run.distance = float(round(total_distance_km, 3))

        if existing_data['count'] > 0:
            first_position = Position.objects.filter(run=run).earliest('date_time')
            run.run_time_seconds = (date_time - first_position.date_time).total_seconds()
        else:
            run.run_time_seconds = 0

        run.save()

        # Сохраняем новую позицию
        serializer.validated_data.update({
            'distance': float(round(total_distance_km, 3)),
            'speed': float(round(new_segment_speed, 2)),
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)