from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from geopy.distance import geodesic
from app_run import models
from app_run.models import Run, RunStatus
from .models import Position
from .serializers import PositionSerializer
from django.db.models import F

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)