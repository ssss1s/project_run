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

        # Получаем все позиции и время начала забега
        positions = Position.objects.filter(run=run).order_by('date_time')
        run_start_time = run.start_time  # Время начала забега из модели Run

        # Инициализация переменных
        total_distance_m = Decimal('0.0')
        valid_segments = []

        # 1. Обработка существующих сегментов
        prev_position = None
        for position in positions:
            if prev_position:
                time_diff = (position.date_time - prev_position.date_time).total_seconds()
                if time_diff > 0:
                    segment_m = Decimal(geodesic(
                        (float(prev_position.latitude), float(prev_position.longitude)),
                        (float(position.latitude), float(position.longitude))
                    ).meters)

                    valid_segments.append({
                        'distance': segment_m,
                        'time': Decimal(str(time_diff)),
                        'speed': segment_m / Decimal(str(time_diff))
                    })
                    total_distance_m += segment_m
            prev_position = position

        # 2. Обработка нового сегмента
        new_segment = {'distance': Decimal('0.0'), 'time': Decimal('0.0'), 'speed': Decimal('0.0')}
        if positions.exists():
            last_position = positions.last()
            time_diff = (date_time - last_position.date_time).total_seconds()

            if time_diff > 0:
                new_segment['distance'] = Decimal(geodesic(
                    (float(last_position.latitude), float(last_position.longitude)),
                    (float(latitude), float(longitude))
                ).meters)
                new_segment['time'] = Decimal(str(time_diff))
                new_segment['speed'] = new_segment['distance'] / new_segment['time']

                valid_segments.append(new_segment)
                total_distance_m += new_segment['distance']

        # 3. Расчет общего времени (от начала забега до последней точки)
        if run_start_time:
            total_time_sec = (date_time - run_start_time).total_seconds()
        else:
            total_time_sec = sum(seg['time'] for seg in valid_segments)

        # 4. Корректный расчет средней скорости
        if total_time_sec > 0:
            average_speed = total_distance_m / Decimal(str(total_time_sec))
        else:
            average_speed = Decimal('0.0')

        # 5. Обновление данных забега
        run.speed = float(round(average_speed, 2))
        run.distance = float(round(total_distance_m / Decimal('1000'), 5))
        run.run_time_seconds = float(total_time_sec)
        run.save()

        # 6. Подготовка данных новой позиции
        serializer.validated_data.update({
            'distance': run.distance,
            'speed': float(round(new_segment['speed'], 2)) if new_segment['time'] > 0 else 0.0,
            'date_time': date_time
        })

        # Отладочная информация
        print(f"\n=== Результаты расчета ===")
        print(f"Общее расстояние: {total_distance_m} м ({run.distance} км)")
        print(f"Общее время: {total_time_sec} сек")
        print(f"Средняя скорость: {average_speed} м/с")
        print(f"Скорость нового сегмента: {new_segment['speed']} м/с")
        print(f"Время начала забега: {run_start_time}")

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)