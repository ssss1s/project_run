from rest_framework import serializers

from the_athlete.models import Athlete
from .models import Run
from django.contrib.auth.models import User

class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Athlete
        fields = '__all__'

class RunSerializer(serializers.ModelSerializer):
    athlete = AthleteSerializer(read_only=True)
    class Meta:
        model = Run
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username',  'first_name', 'last_name', 'type']

    def get_type(self, obj):
            if obj.is_staff:
               return 'coach'
            else:
                return 'athlete'




#Создай endpoint api/users/ , с возможностью фильтра по полю type:

    #Если type = "coach", значит надо вернуть тех юзеров, кто is_staff
    #Если type = "athlete",  вернуть тех, кто не is_staff.
    #Если type не указан (или в нем передано что-то другое)  - вернуть всех.
    #Пользователей с флагом is_superuser не возвращать никогда.
    #Используй ReadOnlyModelViewSet.

#Возвращай не все поля модели User, а только id, date_joined, username, last_name и first_name. И плюс дополнительное поле type.```