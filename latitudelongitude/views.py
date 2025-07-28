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
        total_distance_km = Decimal('0.0')  # Суммарное расстояние в километрах
        segment_speed_mps = Decimal('0.0')  # Скорость текущего сегмента в м/с

        if positions.exists():
            last_position = positions.last()

            # Расчёт расстояния между точками (в метрах)
            segment_m = Decimal(str(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters))

            # Переводим в километры для хранения
            segment_km = segment_m / Decimal('1000')

            # Расчёт времени между точками (в секундах)
            time_diff = (date_time - last_position.date_time).total_seconds()

            # Скорость текущего сегмента (м/с)
            if time_diff > 0:
                segment_speed_mps = segment_m / Decimal(str(time_diff))

            # Суммарное расстояние в км
            total_distance_km = Decimal(str(last_position.distance)) + segment_km

            # Расчёт средней скорости за весь забег (м/с)
            first_position = positions.first()
            total_time_seconds = (date_time - first_position.date_time).total_seconds()

            if total_time_seconds > 0:
                # Общее расстояние в метрах для расчёта скорости
                total_distance_m = total_distance_km * Decimal('1000')
                average_speed_mps = total_distance_m / Decimal(str(total_time_seconds))

                # Обновление данных забега
                run.speed = float(round(average_speed_mps, 2))  # Сохраняем в м/с
                run.run_time_seconds = total_time_seconds
                run.distance = float(round(total_distance_km, 2))  # В км
                run.save()

        # Подготовка данных для сохранения новой точки
        serializer.validated_data.update({
            'distance': float(round(total_distance_km, 2)),  # Сохраняем в км
            'speed': float(round(segment_speed_mps, 2)),  # Скорость в м/с
            'date_time': date_time
        })

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
