from rest_framework import serializers

from subscribe.models import Subscribe
from .models import Run
from django.contrib.auth.models import User
from decimal import Decimal, InvalidOperation


class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username',  'first_name', 'last_name']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = serializers.SerializerMethodField(read_only=True)
    distance = serializers.DecimalField(
        max_digits=6,
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
    runs_finished = serializers.IntegerField(source='runs_finished_count', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'first_name', 'last_name',
                'type', 'runs_finished']

    def get_type(self, obj):
        return 'coach' if obj.is_staff else 'athlete'

class UserDetailSerializer(UserSerializer):
    items = serializers.SerializerMethodField()
    coach = serializers.SerializerMethodField()
    athletes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['items', 'coach','athletes']

    def get_items(self, obj):
        from item.serializers import CollectibleItemSerializer
        return CollectibleItemSerializer(obj.items.all(), many=True).data

    def get_coach(self, obj):
        subscription = Subscribe.objects.filter(athlete=obj).first()
        return subscription.coach.id if subscription else None

    def get_athletes(self, obj):
        subscriptions = Subscribe.objects.filter(coach=obj)
        return list(subscriptions.values_list('athlete_id', flat=True)) if subscriptions else []








