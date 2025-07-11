from rest_framework import serializers
from athlete_info.models import AthleteInfo


class AthleteInfoSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source='Info.id',
        read_only=True
    )

    class Meta:
        model = AthleteInfo
        fields = ['id', 'user_id', 'weight', 'goals']

    def validate_weight(self, value):
        if value <= 0 or value >= 900:
            raise serializers.ValidationError("Вес должен быть между 0 и 900 кг.")
        return value



