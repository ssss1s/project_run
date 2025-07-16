from rest_framework import serializers, status
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
                raise serializers.ValidationError({
                    'latitude': 'Latitude must be between -90 and 90',
                    "status_code": status.HTTP_400_BAD_REQUEST
                }

                )
            return Decimal(str(round(lat, 4)))

        except (TypeError, ValueError):
            raise serializers.ValidationError({
                "message": "Некорректное значение широты. Должно быть числом.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }
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
                    'run': {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Забег должен быть в статусе 'in_progress'"
                    }
                })


            return data

        except ValueError as e:
            error_msg = str(e)
            if 'latitude' in error_msg:
                raise serializers.ValidationError({
                    'latitude': {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message":error_msg.split('\n')[0]}
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