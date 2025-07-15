from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status
from athlete_info.models import ChallengeAthlete
from .models import Run, RunStatus
from .serializers import UserSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from .serializers import RunSerializer
from django.shortcuts import get_object_or_404

class UserPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'size'
    max_page_size = 50
    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get(self.page_size_query_param):
            return super().paginate_queryset(queryset, request, view)
        return None

class RunPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'size'
    max_page_size = 50
    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get(self.page_size_query_param):
            return super().paginate_queryset(queryset, request, view)
        return None

class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related()
    serializer_class = RunSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'athlete']
    ordering_fields =['created_at']
    pagination_class = RunPagination

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['last_name', 'first_name']
    ordering_fields = ['date_joined']
    pagination_class = UserPagination

    def get_queryset(self):
        qs = self.queryset
        user_type = self.request.query_params.get('type', None)
        if user_type == 'coach':
            qs = qs.filter(is_staff=True)
        elif user_type == 'athlete':
            qs = qs.filter(is_staff=False)
        return qs


class RunStartAPIView(APIView):
    def post(self, request, run_id):
        run = get_object_or_404(Run, pk=run_id)

        if run.status != RunStatus.INIT:
            return Response(
                {"error": "Запуск может быть начат только со статуса init"},
                status=status.HTTP_400_BAD_REQUEST
            )

        run.status = RunStatus.IN_PROGRESS
        run.save()
        return Response(
            {"status": "Запуск начался успешно"},
            status=status.HTTP_200_OK
        )


class RunStopAPIView(APIView):
    def post(self, request, run_id):
        run = get_object_or_404(Run, pk=run_id)

        if run.status != RunStatus.IN_PROGRESS:
            return Response(
                {"error": "Запуск может быть остановлен только из состояния in_progress"},
                status=status.HTTP_400_BAD_REQUEST
            )

        run.status = RunStatus.FINISHED
        run.save()

        return Response(
            {"status": "Запуск успешно остановлен"},
            status=status.HTTP_200_OK
        )

@api_view(['GET'])
def company_info(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)



class StopRunView(APIView):
    def post(self, request, run_id):
        try:
            run = Run.objects.select_related('athlete').get(pk=run_id)
            print(f"\n--- Начало обработки остановки забега {run.id} ---")
            print(f"Текущий статус: {run.status}")
            print(f"Атлет: {run.athlete.id}")

            if run.status != RunStatus.IN_PROGRESS:
                print("ОШИБКА: Забег не в статусе IN_PROGRESS")
                return Response(...)

            # Точный подсчёт перед изменением
            finished_before = Run.objects.filter(
                athlete=run.athlete,
                status=RunStatus.FINISHED
            ).count()
            print(f"Завершённых забегов до остановки: {finished_before}")

            run.status = RunStatus.FINISHED
            run.save()
            print(f"Забег {run.id} переведён в FINISHED")

            # Проверка условия
            if finished_before == 9:
                print("УСЛОВИЕ ВЫПОЛНЕНО: Было 9 завершённых забегов")
                challenge, created = ChallengeAthlete.objects.get_or_create(
                    athlete=run.athlete,
                    full_name="Сделай 10 Забегов!",
                    defaults={'athlete': run.athlete, 'full_name': "Сделай 10 Забегов!"}
                )
                if created:
                    print(f"СОЗДАН Challenge ID: {challenge.id}")
                else:
                    print("Challenge уже существовал")
            else:
                print(f"Условие не выполнено (было {finished_before}, нужно 9)")

            return Response(...)

        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            return Response(...)




