from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Position
from .serializers import PositionSerializer
from geopy.distance import geodesic
from app_run.models import Run
from django.utils import timezone
from decimal import Decimal


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'run': ['exact'],  # Явно указываем тип фильтрации
    }

    def get_queryset(self):
        """
        Опционально: можно добавить дополнительную фильтрацию
        """
        queryset = super().get_queryset()
        run_id = self.request.query_params.get('run')
        if run_id:
            queryset = queryset.filter(run_id=run_id)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        run = serializer.validated_data['run']
        latitude = Decimal(str(serializer.validated_data['latitude']))
        longitude = Decimal(str(serializer.validated_data['longitude']))
        date_time = serializer.validated_data.get('date_time', timezone.now())

        previous_positions = Position.objects.filter(run=run).order_by('date_time')
        distance = Decimal('0.0')
        speed = Decimal('0.0')

        if previous_positions.exists():
            last_position = previous_positions.last()

            # Расчет расстояния в метрах
            segment_meters = Decimal(str(geodesic(
                (float(last_position.latitude), float(last_position.longitude)),
                (float(latitude), float(longitude))
            ).meters))

            time_diff = (date_time - last_position.date_time).total_seconds()

            if time_diff > 0:
                speed = segment_meters / Decimal(str(time_diff))

            # Накопленное расстояние
            distance = Decimal(str(last_position.distance)) + segment_meters

            # Округляем до сотых
            distance = round(distance, 2)
            speed = round(speed, 2)

            serializer.validated_data.update({
                'distance': float(distance),
                'speed': float(speed),
                'date_time': date_time
            })

            self.perform_create(serializer)
            self.update_run_average_speed(run.id)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update_run_average_speed(self, run_id):
        positions = Position.objects.filter(run_id=run_id).exclude(speed=0.0)
        if positions.exists():
            avg_speed = sum(p.speed for p in positions) / positions.count()
            Run.objects.filter(id=run_id).update(speed=round(avg_speed, 2))