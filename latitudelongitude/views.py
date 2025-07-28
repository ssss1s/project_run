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
        total_distance_m = Decimal('0.0')  # Суммарное расстояние в метрах
        segment_speed = Decimal('0.0')  # Скорость текущего сегмента

        if positions.exists():
            last_position = positions.last()

            # Расчёт расстояния между текущей и предыдущей точкой (в метрах)
            segment_m = Decimal(str(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters))

            # Расчёт времени между точками (в секундах)
            time_diff = (date_time - last_position.date_time).total_seconds()

            # Скорость текущего сегмента (м/с)
            if time_diff > 0:
                segment_speed = segment_m / Decimal(str(time_diff))

            # Суммарное расстояние (обновляем с учётом нового сегмента)
            total_distance_m = Decimal(str(last_position.distance)) * 1000 + segment_m

            # Расчёт средней скорости за весь забег
            first_position = positions.first()
            total_time_seconds = (date_time - first_position.date_time).total_seconds()

            if total_time_seconds > 0:
                # Средняя скорость в м/с
                average_speed_mps = total_distance_m / Decimal(str(total_time_seconds))
                # Конвертация в км/ч (×3.6)
                average_speed_kmph = average_speed_mps * Decimal('3.6')

                # Обновление данных забега
                run.speed = float(round(average_speed_kmph, 2))
                run.run_time_seconds = total_time_seconds
                run.distance = float(round(total_distance_m / 1000, 2))  # Переводим в км
                run.save()

        # Подготовка данных для сохранения новой точки
        serializer.validated_data.update({
            'distance': float(round(total_distance_m / 1000, 2)),  # Сохраняем в км
            'speed': float(round(segment_speed, 2)),  # Скорость текущего сегмента
            'date_time': date_time
        })

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
