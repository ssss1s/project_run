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
        total_distance_m = Decimal('0.0')
        segment_speed_mps = Decimal('0.0')
        speed_sum = Decimal('0.0')  # Сумма скоростей всех сегментов
        segment_count = 0  # Количество сегментов

        if positions.exists():
            last_position = positions.last()

            # Расчёт текущего сегмента
            segment_m = Decimal(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters)

            time_diff = (date_time - last_position.date_time).total_seconds()
            if time_diff > 0:
                segment_speed_mps = Decimal(segment_m) / Decimal(str(time_diff))
                speed_sum += segment_speed_mps
                segment_count += 1

            # Пересчёт общего расстояния
            total_distance_m = Decimal('0.0')
            prev_point = positions.first()
            speeds = []  # Массив для хранения скоростей всех сегментов

            for i in range(1, len(positions)):
                prev = positions[i - 1]
                curr = positions[i]
                seg_dist = Decimal(geodesic(
                    (float(prev.latitude), float(prev.longitude)),
                    (float(curr.latitude), float(curr.longitude))
                ).meters)
                seg_time = (curr.date_time - prev.date_time).total_seconds()

                if seg_time > 0:
                    seg_speed = seg_dist / Decimal(str(seg_time))
                    speeds.append(seg_speed)

                total_distance_m += seg_dist
                prev_point = curr

            # Добавляем новый сегмент
            total_distance_m += segment_m

            # Расчёт средней скорости как среднее арифметическое
            if speeds:
                # Добавляем скорость текущего сегмента если она > 0
                if segment_speed_mps > 0:
                    speeds.append(segment_speed_mps)

                average_speed_mps = sum(speeds) / Decimal(str(len(speeds)))
            else:
                average_speed_mps = Decimal('0.0')

            # Обновление данных забега
            total_time_sec = (date_time - positions.first().date_time).total_seconds()
            run.speed = float(round(average_speed_mps, 2))
            run.run_time_seconds = float(total_time_sec)
            run.distance = float(round(total_distance_m / 1000, 3))
            run.save()

        # Сохраняем данные новой позиции
        serializer.validated_data.update({
            'distance': float(round(total_distance_m / 1000, 3)),
            'speed': float(round(segment_speed_mps, 2)),
            'date_time': date_time
        })

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)