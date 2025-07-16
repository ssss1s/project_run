from rest_framework import serializers
from .models import Position
from .schemas import PositionCreate, PositionResponse

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'run', 'latitude', 'longitude']
        extra_kwargs = {
            'run': {'required': True}
        }

    def validate(self, data):
        try:
            # Валидация через Pydantic
            PositionCreate(
                run=data['run'].id,
                latitude=data['latitude'],
                longitude=data['longitude']
            )
            return data
        except Exception as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, instance):
        return PositionResponse.from_orm(instance).dict()