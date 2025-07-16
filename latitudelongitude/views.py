from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from latitudelongitude.models import Position
from latitudelongitude.serializers import PositionSerializer
from .schemas import PositionResponse


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['run']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Конвертируем в Pydantic-ответ для строгой схемы
        response_data = PositionResponse.from_orm(serializer.instance).dict()
        return Response(response_data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        # Конвертируем в Pydantic-ответ
        response_data = [PositionResponse.from_orm(pos).dict() for pos in queryset]
        return Response(response_data)