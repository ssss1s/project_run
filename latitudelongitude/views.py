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
        current_time = serializer.validated_data.get('date_time', timezone.now())

        # 1. Находим ближайшую предыдущую точку по времени (не обязательно предыдущую в БД)
        last_position = Position.objects.filter(
            run=run,
            date_time__lt=current_time  # только точки, которые были раньше текущей
        ).order_by('-date_time').first()  # берём самую свежую из предыдущих

        # 2. Инициализация значений для новой точки
        segment_distance = Decimal('0')
        segment_time = Decimal('0')
        segment_speed = Decimal('0')

        if last_position:
            # 3. Расчёт параметров только для этого сегмента
            segment_distance = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

            segment_time = Decimal(str((current_time - last_position.date_time).total_seconds()))

            if segment_time > 0:
                segment_speed = segment_distance / segment_time

        # 4. Обновляем общие показатели трека
        if last_position:
            # Добавляем к общему расстоянию только новый сегмент
            run.distance = (Decimal(str(run.distance or '0')) * 1000) + segment_distance
        else:
            # Это первая точка в треке
            run.distance = Decimal('0')

        # Конвертируем в км и округляем
        run.distance = float(round(run.distance / Decimal('1000'), 5))

        # Общее время (максимальное время между первой и последней точкой)
        if last_position:
            run.run_time_seconds = float(round(
                Decimal(str(run.run_time_seconds or '0')) + segment_time,
                1
            ))
        else:
            run.run_time_seconds = 0.0

        # Пересчёт средней скорости для всего трека
        if run.run_time_seconds > 0:
            run.speed = float(round(
                (Decimal(str(run.distance)) * 1000) / Decimal(str(run.run_time_seconds)),
                2
            ))
        else:
            run.speed = 0.0

        run.save()

        # 5. Подготовка данных для сохранения позиции
        serializer.validated_data.update({
            'distance': run.distance,
            'speed': float(round(segment_speed, 2)),
            'date_time': current_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)