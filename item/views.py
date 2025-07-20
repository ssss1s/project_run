from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
from .models import CollectibleItem
from .serializers import CollectibleItemSerializer


def validate_value(value):
    try:
        num = int(float(str(value)))
        return num >= 0
    except (ValueError, TypeError):
        return False

def validate_coordinate(value, coord_type):
    try:
        coord = Decimal(str(value)).quantize(Decimal('0.000000'))
        if coord_type == 'latitude':
            return -90 <= coord <= 90
        return -180 <= coord <= 180
    except (InvalidOperation, ValueError, TypeError):
        return False

def validate_url(url):
    url = str(url).strip()
    return (url.startswith(('http://', 'https://'))
            and len(url) >= 10
            and ' ' not in url)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    if not file.name.endswith('.xlsx'):
        return Response({"error": "Only XLSX files are supported"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        wb = load_workbook(filename=file)
        ws = wb.active
        invalid_rows = []

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):
                continue

            row_data = list(row)
            is_valid = (
                len(row_data) >= 6 and
                str(row_data[0]) in ['Coin', 'Flag'] and  # Проверка типа
                validate_value(row_data[2]) and
                validate_coordinate(row_data[3], 'latitude') and
                validate_coordinate(row_data[4], 'longitude') and
                validate_url(row_data[5])
            )

            if is_valid:
                CollectibleItem.objects.create(
                    type=str(row_data[0]),
                    uid=str(row_data[1]),
                    value=int(float(str(row_data[2]))),
                    latitude=Decimal(str(row_data[3])),
                    longitude=Decimal(str(row_data[4])),
                    picture=str(row_data[5])
                )
            else:
                invalid_rows.append(list(row_data))  # Важно: преобразуем tuple в list

        # Возвращаем ТОЛЬКО список невалидных строк (без мета-данных)
        return Response(invalid_rows, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
