from rest_framework import serializers
from .models import Run, RunStatus
from django.contrib.auth.models import User

class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username',  'first_name', 'last_name']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = AthleteSerializer(source='athlete', read_only=True)
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = '__all__'
        extra_kwargs = {
            'athlete': {'write_only': True}  # Скрываем в выводе, так как есть athlete_data
        }

    def get_athlete_data(self, obj):
        """Возвращает сериализованные данные пользователя."""
        return AthleteSerializer(obj.athlete).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    def to_internal_value(self, data):
        return super().to_internal_value(data)

class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    runs_finished=serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username',  'first_name', 'last_name', 'type', 'runs_finished']

    def get_type(self, obj):
            if obj.is_staff:
               return 'coach'
            else:
                return 'athlete'

    def get_runs_finished(self, obj):
        return obj.runs.filter(status=RunStatus.FINISHED).count()

#Добавь в API enpoint /api/users/ поле runs_finished в котором будет отображаться для каждого Юзера количество Забегов со статусом finished.


#Создай endpoint api/users/ , с возможностью фильтра по полю type:

    #Если type = "coach", значит надо вернуть тех юзеров, кто is_staff
    #Если type = "athlete",  вернуть тех, кто не is_staff.
    #Если type не указан (или в нем передано что-то другое)  - вернуть всех.
    #Пользователей с флагом is_superuser не возвращать никогда.
    #Используй ReadOnlyModelViewSet.

#Возвращай не все поля модели User, а только id, date_joined, username, last_name и first_name. И плюс дополнительное поле type.```