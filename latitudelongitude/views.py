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
        total_distance_km = Decimal('0.0')
        segment_speed_mps = Decimal('0.0')

        if positions.exists():
            last_position = positions.last()

            # Точный расчёт расстояния в метрах
            segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

            # Точное время в секундах
            time_diff = Decimal(str((date_time - last_position.date_time).total_seconds()))

            # Точный расчёт скорости (Decimal) с округлением до сотых
            if time_diff > 0:
                segment_speed_mps = (segment_m / time_diff).quantize(Decimal('0.01'))

            # Обновление суммарного расстояния
            total_distance_km = Decimal(str(last_position.distance)) + (segment_m / Decimal('1000'))

            # Расчёт средней скорости с округлением до сотых
            first_position = positions.first()
            total_time_sec = Decimal(str((date_time - first_position.date_time).total_seconds()))

            if total_time_sec > 0:
                average_speed_mps = ((total_distance_km * Decimal('1000')) / total_time_sec).quantize(Decimal('0.01'))
                run.speed = float(average_speed_mps)
                run.run_time_seconds = float(total_time_sec)
                run.distance = float(total_distance_km)
                run.save()

        # Сохраняем данные с округлением до сотых
        serializer.validated_data.update({
            'distance': float(total_distance_km),
            'speed': float(segment_speed_mps),  # Округлено до сотых
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
