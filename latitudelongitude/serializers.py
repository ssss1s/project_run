from rest_framework import serializers, status
from .models import Position
from .schemas import PositionCreate


class PositionSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    class Meta:
        model = Position
        fields = ['id', 'run', 'latitude', 'longitude']
        extra_kwargs = {
            'run': {'required': True},
            'latitude': {'required': True},
            'longitude': {'required': True}
        }

    def validate(self, data):
        """Общая валидация с правильной обработкой ошибок Pydantic"""
        try:
            # Валидация через Pydantic
            PositionCreate(
                run=data['run'].id,
                latitude=float(data['latitude']),
                longitude=float(data['longitude'])
            )

            # Дополнительная проверка статуса забега
            if data['run'].status != 'in_progress':
                raise serializers.ValidationError({
                    'run': {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Забег должен быть в статусе 'in_progress'",
                        "code": "invalid_run_status"
                    }
                })

            return data

        except ValueError as e:
            # Обработка ошибок Pydantic
            error_msg = str(e)
            if "Забег должен быть в статусе 'in_progress'" in error_msg:
                raise serializers.ValidationError({
                    'run': {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": "Забег должен быть в статусе 'in_progress'",
                        "code": "invalid_run_status"
                    }
                })
            elif 'latitude' in error_msg:
                raise serializers.ValidationError({
                    'latitude': {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": error_msg.split('\n')[0],
                        "code": "invalid_latitude"
                    }
                })
            elif 'longitude' in error_msg:
                raise serializers.ValidationError({
                    'longitude': {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "message": error_msg.split('\n')[0],
                        "code": "invalid_longitude"
                    }
                })

            raise serializers.ValidationError({
                "non_field_errors": {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": error_msg,
                    "code": "validation_error"
                }
            })