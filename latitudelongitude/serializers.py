# serializers.py
from rest_framework import serializers
from latitudelongitude.models import Position
from app_run.models import Run
from .schemas import PositionCreate, RunStatus


class PositionSerializer(serializers.ModelSerializer):
    run = serializers.PrimaryKeyRelatedField(queryset=Run.objects.all())

    class Meta:
        model = Position
        fields = ['id', 'run', 'latitude', 'longitude']
        read_only_fields = ['id']

    def validate(self, data):
        """Валидация через Pydantic + проверка статуса забега."""
        try:
            # Конвертируем данные в Pydantic-модель
            pydantic_data = PositionCreate(**data)
            data = pydantic_data.dict(by_alias=True)  # {"run": ...} → {"run_id": ...}

            # Проверяем статус забега
            run = data["run"]
            if run.status != RunStatus.IN_PROGRESS:
                raise serializers.ValidationError("Забег должен быть в статусе 'in_progress'.")

            return data
        except Exception as e:
            raise serializers.ValidationError(str(e))