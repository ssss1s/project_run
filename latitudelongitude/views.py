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

        # 1. Извлечение данных
        run = serializer.validated_data['run']
        latitude = Decimal(str(serializer.validated_data['latitude']))
        longitude = Decimal(str(serializer.validated_data['longitude']))
        date_time = serializer.validated_data.get('date_time', timezone.now())

        # 2. Получение существующих позиций
        positions = Position.objects.filter(run=run).order_by('date_time')

        # 3. Если это первая позиция в треке
        if not positions.exists():
            # Устанавливаем нулевые значения
            run.distance = 0.0
            run.speed = 0.0
            run.run_time_seconds = 0.0
            run.save()

            # Сохраняем позицию с нулевыми значениями
            serializer.validated_data.update({
                'distance': 0.0,
                'speed': 0.0
            })
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # 4. Если это не первая позиция - расчет параметров
        last_position = positions.last()

        # Расчет временного интервала (в секундах)
        time_diff = Decimal(str((date_time - last_position.date_time).total_seconds()))

        # Расчет расстояния между точками (в метрах)
        distance_m = Decimal(geodesic(
            (float(last_position.latitude), float(last_position.longitude)),
            (float(latitude), float(longitude))
        ).meters)

        # Фильтрация аномальных значений
        MIN_TIME_DIFF = Decimal('5.0')  # Минимум 5 секунд
        MIN_DISTANCE = Decimal('10.0')  # Минимум 10 метров
        MAX_SPEED = Decimal('55.56')  # Максимум 200 км/ч (55.56 м/с)

        if time_diff >= MIN_TIME_DIFF and distance_m >= MIN_DISTANCE:
            speed = distance_m / time_diff
            if speed <= MAX_SPEED:
                # Обновляем общую дистанцию трека (в км)

                run.save()

                # Данные для сохранения позиции
                serializer.validated_data.update({
                    'distance': float(distance_m / Decimal('1000')),
                    'speed': float(speed)
                })

                self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)