from rest_framework import serializers
from decimal import Decimal
from item.models import CollectibleItem


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = '__all__'
        extra_kwargs = {'uid': {'validators': []}}

    def validate_latitude(self, value):
        try:
            value = Decimal(str(value))
            if not -90 <= value <= 90:
                raise ValueError("Широта должна быть от -90 до 90")
            return value
        except:
            raise serializers.ValidationError("Некорректная широта")

    def validate_longitude(self, value):
        try:
            value = Decimal(str(value))
            if not -180 <= value <= 180:
                raise ValueError("Долгота должна быть от -180 до 180")
            return value
        except:
            raise serializers.ValidationError("Некорректная долгота")

    def validate_picture(self, value):
        if not value.startswith(('http://', 'https://')):
            value = f'https://{value}'
        return value

    def validate_value(self, value):
        try:
            return int(float(str(value)))
        except:
            raise serializers.ValidationError("Значение должно быть числом")