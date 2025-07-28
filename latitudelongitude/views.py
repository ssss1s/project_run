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

        # Получаем ВСЕ позиции забега в хронологическом порядке
        positions = Position.objects.filter(run=run).order_by('date_time')
        total_distance_m = Decimal('0.0')  # Общее расстояние в метрах
        segment_speed_mps = Decimal('0.0')  # Скорость текущего сегмента

        if positions.exists():
            last_position = positions.last()

            # 1. Расчёт расстояния между последней и новой точкой
            segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

            # 2. Расчёт времени между последней и новой точкой
            time_diff = (date_time - last_position.date_time).total_seconds()
            if time_diff > 0:
                segment_speed_mps = Decimal(segment_m) / Decimal(str(time_diff))

            # 3. Пересчёт общего расстояния (важно!)
            # Собираем все отрезки заново для точности
            total_distance_m = Decimal('0.0')
            prev_point = positions.first()
            for point in positions[1:]:
                total_distance_m += Decimal(geodesic(
                    (float(prev_point.latitude), float(prev_point.longitude)),
                    (float(point.latitude), float(point.longitude))
                ).meters)
                prev_point = point

            # Добавляем новый сегмент
            total_distance_m += segment_m

            # 4. Расчёт общего времени забега
            first_position = positions.first()
            total_time_sec = (date_time - first_position.date_time).total_seconds()

            if total_time_sec > 0:
                # Средняя скорость (м/с)
                average_speed_mps = total_distance_m / Decimal(str(total_time_sec))

                # Обновляем данные забега
                run.speed = float(round(average_speed_mps, 2))
                run.run_time_seconds = float(total_time_sec)
                run.distance = float(round(total_distance_m / 1000, 3))  # в км с округлением
                run.save()

        # Сохраняем данные новой позиции
        serializer.validated_data.update({
            'distance': float(round(total_distance_m / 1000, 3)),  # в км
            'speed': float(round(segment_speed_mps, 2)),  # скорость сегмента
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
