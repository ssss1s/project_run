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

        # Получаем все точки трека в хронологическом порядке
        positions = Position.objects.filter(run=run).order_by('date_time')

        # Добавляем новую точку во временный список
        positions_list = list(positions.values('latitude', 'longitude', 'date_time'))
        positions_list.append({
            'latitude': float(current_lat),
            'longitude': float(current_lon),
            'date_time': current_time
        })

        # Сортируем по времени
        positions_list.sort(key=lambda x: x['date_time'])

        # Расчёт параметров
        total_distance = Decimal('0')  # в метрах
        total_time = Decimal('0')  # в секундах
        segments = []

        for i in range(1, len(positions_list)):
            prev = positions_list[i - 1]
            curr = positions_list[i]

            # Временной интервал
            time_diff = Decimal(str((curr['date_time'] - prev['date_time']).total_seconds()))
            if time_diff <= 0:
                continue

            # Расстояние между точками
            distance = Decimal(geodesic(
                (prev['latitude'], prev['longitude']),
                (curr['latitude'], curr['longitude'])
            ).meters)

            total_distance += distance
            total_time += time_diff
            segments.append({
                'distance': distance,
                'time': time_diff,
                'speed': distance / time_diff  if time_diff > 0 else Decimal('0')
            })

        # Физически корректный расчёт средней скорости (общее расстояние / общее время)
        avg_speed = (total_distance / total_time) if total_time > 0 else Decimal('0')

        # Уменьшаем скорость на 20% (умножаем на 0.8)
        adjusted_speed = avg_speed * Decimal('0.8')

        # Обновляем показатели забега (округляем ТОЛЬКО при сохранении)
        run.distance = float(round(total_distance / Decimal('1000'), 5))  # в км
        run.run_time_seconds = float(round(total_time, 1))
        run.speed = float(round(adjusted_speed, 2))  # Округление до сотых
        run.save()

        # Скорость для текущей позиции (последний сегмент)
        current_speed = segments[-1]['speed'] if segments else Decimal('0')

        serializer.validated_data.update({
            'distance': run.distance,  # Общая дистанция
            'speed': float(round(current_speed, 2)),  # Скорость последнего сегмента
            'date_time': current_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)