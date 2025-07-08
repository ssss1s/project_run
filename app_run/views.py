from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Run
from .serializers import RunSerializer, UserSerializer
from rest_framework.filters import SearchFilter


class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related()
    serializer_class = RunSerializer
    filter_backends = [SearchFilter]
    search_fields = ['last_name', 'first_name']

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = UserSerializer


    def get_queryset(self):
        qs = self.queryset
        user_type = self.request.query_params.get('type', None)
        if user_type == 'coach':
            qs = qs.filter(is_staff=True)
        elif user_type == 'athlete':
            qs = qs.filter(is_staff=False)
        return qs


@api_view(['GET'])
def company_info(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)





