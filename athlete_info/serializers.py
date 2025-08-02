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


from rest_framework import serializers
from django.contrib.auth.models import User


class AthleteSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        name_parts = []
        if obj.first_name:
            name_parts.append(obj.first_name)
        if obj.last_name:
            name_parts.append(obj.last_name)
        return ' '.join(name_parts) if name_parts else None


class ChallengeSummarySerializer(serializers.Serializer):
    name_to_display = serializers.CharField(source='full_name')
    athletes = AthleteSerializer(many=True)