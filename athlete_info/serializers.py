from rest_framework import serializers
from athlete_info.models import AthleteInfo, ChallengeAthlete
from django.contrib.auth.models import User



class AthleteInfoSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        source='Info.id',
        read_only=True
    )

    class Meta:
        model = AthleteInfo
        fields = ['id', 'user_id', 'weight', 'goals']
        extra_kwargs = {
            'weight': {'required': False, 'allow_null': True},
            'goals': {'required': False, 'allow_null': True}
        }

    def validate_weight(self, value):
        if value <= 0 or value >= 900:
            raise serializers.ValidationError("Вес должен быть между 0 и 900 кг.")
        return value



class ChallengeAthleteSerializer(serializers.ModelSerializer):
    athlete = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ChallengeAthlete
        fields= ['id', 'athlete', 'full_name']
