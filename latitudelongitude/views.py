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

        # Получаем существующие позиции
        positions = Position.objects.filter(run=run).order_by('date_time')
        first_position = positions.first() if positions.exists() else None

        # Расчёт нового сегмента
        new_segment_m = Decimal('0.0')
        if positions.exists():
            last_position = positions.last()
            new_segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

        # Общее расстояние (метры)
        total_distance_m = (positions.aggregate(sum=Sum('distance'))['sum'] or 0) * 1000 + new_segment_m

        # Общее время (секунды)
        if first_position:
            total_time_sec = (date_time - first_position.date_time).total_seconds()
        else:
            total_time_sec = 0

        # Правильный расчёт средней скорости
        average_speed = float(total_distance_m / Decimal(str(total_time_sec))) if total_time_sec > 0 else 0.0

        # Скорость текущего сегмента
        new_segment_speed = 0.0
        if positions.exists():
            time_diff = (date_time - last_position.date_time).total_seconds()
            if time_diff > 0:
                new_segment_speed = float(new_segment_m / time_diff)

        # Обновление забега
        run.speed = round(average_speed, 2)  # 1.24 вместо 1.54
        run.distance = float(total_distance_m / 1000)
        run.run_time_seconds = total_time_sec
        run.save()

        # Сохранение позиции
        serializer.validated_data.update({
            'distance': run.distance,
            'speed': round(new_segment_speed, 2),
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)