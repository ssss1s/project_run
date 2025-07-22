from rest_framework import serializers
from item.models import CollectibleItem
from decimal import Decimal, InvalidOperation
import re
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = ['id', 'name', 'uid', 'latitude', 'longitude', 'picture', 'value']

    VALID_ITEM_TYPES = ['Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn']

    def validate_name(self, value):
        if value not in self.VALID_ITEM_TYPES:
            raise serializers.ValidationError(
                f"Name must be one of: {', '.join(self.VALID_ITEM_TYPES)}"
            )
        return value

    def validate_uid(self, value):
        if len(value) != 8:
            raise serializers.ValidationError("UID must be exactly 8 characters long")

        if not re.fullmatch(r'^[a-f0-9]{8}$', value.lower()):
            raise serializers.ValidationError("UID must consist of 8 hex characters")

        return value.lower()

    def validate_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Value must be greater than 0")
        return value

    def validate_latitude(self, value):
        try:
            decimal_value = Decimal(str(value)).quantize(Decimal('0.000000'))
            if not -90 <= decimal_value <= 90:
                raise serializers.ValidationError("Latitude must be between -90 and 90")
            return decimal_value
        except (InvalidOperation, ValueError, TypeError):
            raise serializers.ValidationError("Invalid latitude value")

    def validate_longitude(self, value):
        try:
            decimal_value = Decimal(str(value)).quantize(Decimal('0.000000'))
            if not -180 <= decimal_value <= 180:
                raise serializers.ValidationError("Longitude must be between -180 and 180")
            return decimal_value
        except (InvalidOperation, ValueError, TypeError):
            raise serializers.ValidationError("Invalid longitude value")

    def validate_picture(self, value):
        validator = URLValidator()
        try:
            validator(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid URL format")

        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")

        return value

    def validate(self, data):
        # Дополнительная проверка на уникальность UID
        if CollectibleItem.objects.filter(uid=data['uid']).exists():
            raise serializers.ValidationError({"uid": "This UID already exists"})
        return data

