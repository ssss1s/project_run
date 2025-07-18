from rest_framework import serializers
from .models import Run, RunStatus
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation
from django.db.models import Sum
import logging  # Добавляем импорт

logger = logging.getLogger(__name__)  # Создаем логгер

class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username',  'first_name', 'last_name']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = serializers.SerializerMethodField(read_only=True)
    distance = serializers.DecimalField(
        max_digits=100,
        decimal_places=3,
        rounding='ROUND_HALF_UP',
        default=0,
        coerce_to_string=True,  # Сериализует Decimal в строку
    )

    class Meta:
        model = Run
        fields = '__all__'
        extra_kwargs = {
            'athlete': {'write_only': True}
        }

    def get_athlete_data(self, obj):
        """Сериализуем данные атлета с помощью AthleteSerializer."""
        return AthleteSerializer(obj.athlete).data

    def to_representation(self, instance):
        """Переопределяем представление для строкового distance."""
        representation = super().to_representation(instance)

        # Явное преобразование в строку (дополнительная страховка)
        if 'distance' in representation and representation['distance'] is not None:
            representation['distance'] = str(
                Decimal(representation['distance']).quantize(Decimal('0.000')))

        return representation

    def to_internal_value(self, data):
        """Обрабатываем входящие данные перед валидацией."""
        if 'distance' in data and data['distance'] is not None:
            try:
                # Принимаем и строки, и числа
                data['distance'] = Decimal(str(data['distance'])).quantize(Decimal('0.000'))
            except (ValueError, TypeError, InvalidOperation):
                raise serializers.ValidationError({
                    'distance': 'Должно быть числом с максимум 2 знаками после запятой'
                })

        return super().to_internal_value(data)

class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    runs_finished=serializers.SerializerMethodField()
    runs_distance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username',  'first_name', 'last_name', 'type', 'runs_finished', 'runs_distance']

    def get_type(self, obj):
            if obj.is_staff:
               return 'coach'
            else:
                return 'athlete'

    def get_runs_finished(self, obj):
        return obj.runs.filter(status=RunStatus.FINISHED).count()

    def get_runs_distance(self, obj):
        try:
            # Получаем сумму дистанций
            result = obj.runs.aggregate(total=Sum('distance'))
            total = result['total']

            # Обработка None значения
            if total is None:
                return "0.000"

            # Проверка типа данных
            if not isinstance(total, (Decimal, float, int)):
                raise ValueError(f"Некорректный тип данных расстояния: {type(total)}")

            # Преобразование в Decimal для точного округления
            try:
                decimal_total = Decimal(str(total))
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f"Невозможно преобразовать значение '{total}' в Decimal") from e

            # Валидация диапазона значений
            if decimal_total < 0:
                raise ValueError("Дистанция не может быть отрицательной")

            # Округление до 3 знаков и форматирование
            rounded_total = decimal_total.quantize(Decimal('0.000'))
            return f"{rounded_total:.3f}"

        except Exception as e:
            # Логирование ошибки для отладки
            logger.error(f"Ошибка при расчете дистанции для пользователя {obj.id}: {str(e)}")
            # Возвращаем значение по умолчанию в продакшене
            return "0.000"  # Или можно пробросить ошибку дальше


        #Добавь в API enpoint /api/users/ поле runs_finished в котором будет отображаться для каждого Юзера количество Забегов со статусом finished.


#Создай endpoint api/users/ , с возможностью фильтра по полю type:

    #Если type = "coach", значит надо вернуть тех юзеров, кто is_staff
    #Если type = "athlete",  вернуть тех, кто не is_staff.
    #Если type не указан (или в нем передано что-то другое)  - вернуть всех.
    #Пользователей с флагом is_superuser не возвращать никогда.
    #Используй ReadOnlyModelViewSet.

#Возвращай не все поля модели User, а только id, date_joined, username, last_name и first_name. И плюс дополнительное поле type.```