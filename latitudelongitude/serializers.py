from rest_framework import serializers
from decimal import Decimal
from .models import Position
from .schemas import PositionCreate, PositionResponse



class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'run', 'latitude', 'longitude']
        extra_kwargs = {
            'run': {'required': True},
            'latitude': {'required': True},
            'longitude': {'required': True}
        }

    def validate_latitude(self, value):
        try:
            lat = float(value)
            if not -90.0 <= lat <= 90.0:
                raise serializers.ValidationError(
                    "Широта должна быть между -90.0 и 90.0 градусами"
                )
            return Decimal(str(round(lat, 4)))

        except (TypeError, ValueError):
            raise serializers.ValidationError(
                "Некорректное значение широты. Должно быть числом."
            )

    def validate(self, data):
        try:
            pydantic_data = PositionCreate(
                run=data['run'].id,
                latitude=float(data['latitude']),
                longitude=float(data['longitude'])
            )

            if data['run'].status != 'in_progress':
                raise serializers.ValidationError({
                    'run': "Забег должен быть в статусе 'in_progress'"
                })

            return data

        except ValueError as e:
            error_msg = str(e)
            if 'latitude' in error_msg:
                raise serializers.ValidationError({
                    'latitude': error_msg.split('\n')[0]
                })
            raise serializers.ValidationError(error_msg)

        except Exception as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, instance):
        response_data = {
            'id': instance.id,
            'run': instance.run_id,
            'latitude': float(instance.latitude),
            'longitude': float(instance.longitude)
        }
        return PositionResponse(**response_data).dict()