from decimal import Decimal, InvalidOperation

from rest_framework import serializers
from item.models import CollectibleItem

class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = ['id','name', 'uid', 'latitude', 'longitude', 'picture', 'value']

    def validate_latitude(self, value):
        try:
            return Decimal(value).quantize(Decimal('0.000000'))
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Некорректный формат широты. Пример: -34.609000")

    def validate_longitude(self, value):
        try:
            return Decimal(value).quantize(Decimal('0.000000'))
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError("Некорректный формат долготы. Пример: -58.370200")


