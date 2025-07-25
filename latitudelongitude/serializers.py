from datetime import datetime
from rest_framework import serializers
from .models import Position
from .schemas import PositionCreate, PositionResponse
from decimal import Decimal


class PositionSerializer(serializers.ModelSerializer):
    date_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%f')

    class Meta:
        model = Position
        fields = ['id', 'run', 'latitude', 'longitude', 'date_time', 'distance', 'speed']

    def validate_latitude(self, value):
        """Валидация широты с преобразованием в float"""
        try:
            lat = float(value)
            if not -90 <= lat <= 90:
                raise serializers.ValidationError(
                    detail="Широта должна быть между -90 и 90 градусами",
                    code="invalid_latitude_range"
                )
            return Decimal(str(lat)).quantize(Decimal('0.0001'))
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                detail="Широта должна быть числовым значением",
                code="invalid_latitude_format"
            )

    def validate_longitude(self, value):
        """Валидация долготы с преобразованием в float"""
        try:
            lon = float(value)
            if not -180 <= lon <= 180:
                raise serializers.ValidationError(
                    detail="Долгота должна быть между -180 и 180 градусами",
                    code="invalid_longitude_range"
                )
            return Decimal(str(lon)).quantize(Decimal('0.0001'))
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                detail="Долгота должна быть числовым значением",
                code="invalid_longitude_format"
            )

    def validate_run(self, value):
        """Проверка существования забега и его статуса"""
        if not value:
            raise serializers.ValidationError(
                detail="Забег обязателен",
                code="missing_run"
            )

        if value.status != 'in_progress':
            raise serializers.ValidationError(
                detail="Забег должен быть в статусе 'in_progress'",
                code="invalid_run_status"
            )
        return value

    def to_internal_value(self, data):
        """Подготовка данных для Pydantic валидации"""
        try:
            data = super().to_internal_value(data)

            # Приводим координаты к float для Pydantic
            data['latitude'] = float(data['latitude'])
            data['longitude'] = float(data['longitude'])

            return data
        except (ValueError, TypeError) as e:
            raise serializers.ValidationError(
                detail=str(e),
                code="invalid_data_format"
            )

    def validate(self, attrs):
        """Финальная валидация через Pydantic"""
        try:
            # Создаем временный словарь для Pydantic
            pydantic_data = {
                'run': attrs['run'].id,
                'latitude': attrs['latitude'],
                'longitude': attrs['longitude'],
                'distance': attrs.get('distance', 0.0),
                'speed': attrs.get('speed', 0.0)
            }

            # Валидация через Pydantic
            PositionCreate(**pydantic_data)

            return attrs
        except ValueError as e:
            error_msg = str(e)
            if "Забег не существует" in error_msg:
                raise serializers.ValidationError(
                    {'run': "Указанный забег не существует"},
                    code="run_not_found"
                )
            raise serializers.ValidationError(
                detail=error_msg,
                code="validation_error"
            )

    def to_representation(self, instance):
        """Преобразование для ответа через Pydantic"""
        representation = super().to_representation(instance)
        return PositionResponse(**representation).dict()

    def validate_date_time(self, value, pytz=None):
        """Дополнительная валидация даты"""
        if not isinstance(value, datetime):
            try:
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                raise serializers.ValidationError(
                    "Неверный формат даты. Используйте YYYY-MM-DDThh:mm:ss.ffffff"
                )

        if value.tzinfo is None:
            value = pytz.UTC.localize(value)
        return value

    def to_representation(self, instance):
        """Гарантируем правильный формат в ответе"""
        ret = super().to_representation(instance)
        if 'date_time' in ret and isinstance(ret['date_time'], datetime):
            ret['date_time'] = ret['date_time'].strftime('%Y-%m-%dT%H:%M:%S.%f')
        return ret