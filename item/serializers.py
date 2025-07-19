from rest_framework import serializers, status
from item.models import CollectibleItem
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal, InvalidOperation


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = '__all__'
        extra_kwargs = {
            'uid': {'validators': []},  # Отключаем уникальность при валидации
        }

    # Методы валидации должны быть НА УРОВНЕ КЛАССА (не внутри Meta)
    def validate_latitude(self, value):
        try:
            lat = Decimal(str(value))  # Явное преобразование в строку для Decimal
            if not Decimal('-90') <= lat <= Decimal('90'):
                raise serializers.ValidationError({
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Latitude must be between -90 and 90 degrees."
                })
            return lat
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid latitude value. Must be a decimal number."
            })

    def validate_longitude(self, value):
        try:
            lon = Decimal(str(value))
            if not Decimal('-180') <= lon <= Decimal('180'):
                raise serializers.ValidationError({
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Longitude must be between -180 and 180 degrees."
                })
            return lon
        except (InvalidOperation, TypeError):
            raise serializers.ValidationError({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid longitude value. Must be a decimal number."
            })

    def validate_picture(self, value):
        validator = URLValidator()
        try:
            validator(value)
            return value
        except DjangoValidationError:
            raise serializers.ValidationError({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid URL format for picture."
            })

    def validate_value(self, value):
        if value < 0:
            raise serializers.ValidationError({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Value must be a positive integer."
            })
        return value