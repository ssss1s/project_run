from datetime import datetime
from rest_framework import serializers
from .models import Position
from decimal import Decimal


class PositionSerializer(serializers.ModelSerializer):
    date_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%f')

    class Meta:
        model = Position
        fields = '__all__'


