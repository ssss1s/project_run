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

        # 1. Получаем и анализируем существующие позиции
        positions = Position.objects.filter(run=run).order_by('date_time')
        segments = []

        # 2. Точный расчет всех сегментов (без округления)
        for i in range(1, len(positions)):
            prev = positions[i - 1]
            curr = positions[i]
            time_diff = (curr.date_time - prev.date_time).total_seconds()

            if time_diff > 0:
                distance_m = Decimal(geodesic(
                    (float(prev.latitude), float(prev.longitude)),
                    (float(curr.latitude), float(curr.longitude))
                ).meters)

                segments.append({
                    'distance': distance_m,
                    'time': Decimal(str(time_diff)),
                    'speed': distance_m / Decimal(str(time_diff))  # Без округления
                })

        # 3. Расчет нового сегмента
        new_segment = {'distance': Decimal('0'), 'time': Decimal('0'), 'speed': Decimal('0')}
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
                segments.append(new_segment)

        # 4. Расчет итоговых значений (без округления)
        total_distance_m = sum(seg['distance'] for seg in segments)
        total_time_sec = sum(seg['time'] for seg in segments)
        total_distance_km = total_distance_m / Decimal('1000')

        # 5. Физически корректный расчет средней скорости
        average_speed = total_distance_m / total_time_sec if total_time_sec > 0 else Decimal('0')

        # 6. Финальное округление ТОЛЬКО при сохранении
        run.speed = float(round(average_speed, 2))  # Округление до сотых
        run.distance = float(round(total_distance_km, 5))  # 5 знаков для точности в км
        run.run_time_seconds = float(round(total_time_sec, 1))  # Округление времени до 0.1 сек
        run.save()

        # 7. Подготовка данных для новой позиции
        current_speed = float(round(new_segment['speed'], 2)) if new_segment['time'] > 0 else 0.0
        serializer.validated_data.update({
            'distance': float(round(total_distance_km, 5)),  # Соответствует сохраненному в run
            'speed': current_speed,
            'date_time': date_time
        })

        # 8. Валидация округлений
        print(f"\n=== Проверка округлений ===")
        print(f"Исходная средняя скорость: {average_speed}")
        print(f"После округления: {run.speed}")
        print(f"Исходная дистанция: {total_distance_km} км")
        print(f"После округления: {run.distance} км")

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)