from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def company_info(request):
    details = {
        'name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)
