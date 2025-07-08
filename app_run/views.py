from django.conf import settings
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status
from .models import Run, RunStatus
from .serializers import UserSerializer
from rest_framework.filters import SearchFilter
from .serializers import RunSerializer
from django.shortcuts import get_object_or_404



class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related()
    serializer_class = RunSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserSerializer
    filter_backends = [SearchFilter]
    search_fields = ['last_name', 'first_name']


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
                {"error": "Run can only be started from 'init' status"},
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
            {
                "status": "Запуск успешно завершен",
                "details": {
                    "run_id": run.id,
                    "duration": str(run.updated_at - run.created_at)
                }
            },
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





