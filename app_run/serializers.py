from rest_framework import serializers

from athlete_info.models import ChallengeAthlete
from .models import Run, RunStatus
from django.contrib.auth.models import User

class AthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username',  'first_name', 'last_name']

class RunSerializer(serializers.ModelSerializer):
    athlete_data = AthleteSerializer(source='athlete', read_only=True)
    class Meta:
        model = Run
        fields = '__all__'

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
        finished_runs = obj.runs.filter(status=RunStatus.FINISHED).count()

        if (
                finished_runs == 10
                and not ChallengeAthlete.objects.filter(athlete=obj).exists()
        ):
            # Создаём запись с кастомным full_name
            ChallengeAthlete.objects.create(
                full_name="Сделай 10 Забегов!",  # Жёстко заданное значение
                athlete=obj
            )

            # Если нужно вызвать StopRunView.post()
            from django.test import RequestFactory
            from .views import StopRunView

            # Создаём фейковый запрос (может потребоваться донастройка)
            request = RequestFactory().post(
                '/fake-path/',  # Любой URL (не влияет на логику)
                data={'user_id': obj.id}  # Передаём данные, если нужно
            )
            request.user = obj  # Если вьюха требует аутентификации

            # Вызываем вьюху
            StopRunView.as_view()(request)  # Или StopRunView().post(request)

        return finished_runs

#Добавь в API enpoint /api/users/ поле runs_finished в котором будет отображаться для каждого Юзера количество Забегов со статусом finished.


#Создай endpoint api/users/ , с возможностью фильтра по полю type:

    #Если type = "coach", значит надо вернуть тех юзеров, кто is_staff
    #Если type = "athlete",  вернуть тех, кто не is_staff.
    #Если type не указан (или в нем передано что-то другое)  - вернуть всех.
    #Пользователей с флагом is_superuser не возвращать никогда.
    #Используй ReadOnlyModelViewSet.

#Возвращай не все поля модели User, а только id, date_joined, username, last_name и first_name. И плюс дополнительное поле type.```