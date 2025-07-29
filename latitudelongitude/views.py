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

        # 1. Извлечение и подготовка данных
        run = serializer.validated_data['run']
        latitude = Decimal(str(serializer.validated_data['latitude']))
        longitude = Decimal(str(serializer.validated_data['longitude']))
        date_time = serializer.validated_data.get('date_time', timezone.now())

        # 2. Получение существующих позиций с оптимизацией запроса
        positions = Position.objects.filter(run=run).order_by('date_time').only(
            'latitude', 'longitude', 'date_time'
        )

        # 3. Параметры фильтрации шумов
        MIN_TIME_DIFF = Decimal('5.0')  # 5 секунд между точками
        MIN_DISTANCE = Decimal('10.0')  # 10 метров минимальное перемещение
        MAX_SPEED = Decimal('55.56')  # 200 км/ч в м/с (фильтр аномалий)

        # 4. Расчет всех сегментов с фильтрацией
        valid_segments = []
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]

            time_diff = Decimal(str((curr.date_time - prev.date_time).total_seconds()))
            distance_m = Decimal(geodesic(
                (float(prev.latitude), float(prev.longitude)),
                (float(curr.latitude), float(curr.longitude))
            ).meters)

            # Фильтрация невалидных сегментов
            if (time_diff >= MIN_TIME_DIFF and
                    distance_m >= MIN_DISTANCE):
                speed = distance_m / time_diff
                if speed <= MAX_SPEED:  # Отсеиваем аномалии
                    valid_segments.append({
                        'distance': distance_m,
                        'time': time_diff,
                        'speed': speed
                    })

        # 5. Обработка новой точки
        new_segment = None
        if positions.exists():
            last_position = positions.last()
            time_diff = Decimal(str((date_time - last_position.date_time).total_seconds()))
            distance_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

            if (time_diff >= MIN_TIME_DIFF and
                    distance_m >= MIN_DISTANCE):
                speed = distance_m / time_diff
                if speed <= MAX_SPEED:
                    new_segment = {
                        'distance': distance_m,
                        'time': time_diff,
                        'speed': speed
                    }
                    valid_segments.append(new_segment)

        # 6. Расчет итоговых показателей
        total_stats = {
            'distance_m': sum(seg['distance'] for seg in valid_segments),
            'time_sec': sum(seg['time'] for seg in valid_segments),
            'speeds': [seg['speed'] for seg in valid_segments]
        }

        # 7. Усреднение скорости (скользящее среднее последних 5 сегментов)
        def calculate_smoothed_speed(speeds, window_size=5):
            recent_speeds = speeds[-window_size:]
            if not recent_speeds:
                return Decimal('0')
            return sum(recent_speeds) / Decimal(str(len(recent_speeds)))

        smoothed_speed = calculate_smoothed_speed(total_stats['speeds'])

        # 8. Обновление объекта Run
        run.distance = float(round(total_stats['distance_m'] / Decimal('1000'), 5))  # в км
        run.run_time_seconds = float(round(total_stats['time_sec'], 1))
        run.speed = float(round(smoothed_speed, 2))  # Средняя скорость последних сегментов
        run.save()

        # 9. Подготовка данных для сохранения позиции
        current_speed = float(round(new_segment['speed'], 2)) if new_segment else 0.0
        serializer.validated_data.update({
            'distance': run.distance,
            'speed': current_speed,
            'date_time': date_time,
        })

        # 10. Логирование для отладки
        debug_info = {
            'total_points': len(valid_segments),
            'filtered_out': len(positions) - len(valid_segments) - 1,
            'last_speed': current_speed,
            'smoothed_speed': run.speed
        }
        print(f"\n[DEBUG] {debug_info}")

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)