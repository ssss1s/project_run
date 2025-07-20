from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError
from item.models import CollectibleItem
from rest_framework import status, viewsets
import re

from item.serializers import CollectibleItemSerializer

# Строгий список разрешенных типов предметов
VALID_ITEM_TYPES = ['Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn']

def validate_type(value):
    """Проверка типа предмета"""
    return str(value) in VALID_ITEM_TYPES

def validate_uid(value):
    """Строгая проверка формата UID (8 hex-символов)"""
    return bool(re.fullmatch(r'^[a-f0-9]{8}$', str(value).lower()))

def validate_value(value):
    """Проверка значения (только положительные целые числа)"""
    try:
        num = int(float(str(value)))
        return num > 0
    except (ValueError, TypeError):
        return False

def validate_coordinate(value, coord_type):
    """Проверка координат с точностью до 6 знаков"""
    try:
        coord = Decimal(str(value)).quantize(Decimal('0.000000'))
        if coord_type == 'latitude':
            return -90 <= coord <= 90
        return -180 <= coord <= 180
    except (InvalidOperation, ValueError, TypeError):
        return False

def validate_url(url):
    """Строгая проверка URL"""
    url = str(url).strip()
    return (
        url.startswith(('http://', 'https://')) and
        len(url) >= 10 and
        ' ' not in url and
        '.' in url and
        '::' not in url and
        not url.endswith(';') and  # Запрещаем точку с запятой в конце
        re.match(r'^https?://[^\s/$.?#].[^\s]*$', url)  # Проверка общего формата URL
    )

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
        seen_uids = set()  # Для отслеживания уникальности UID

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):
                continue

            row_data = list(row)
            if len(row_data) < 6:
                invalid_rows.append(row_data)
                continue

            # Проверка уникальности UID в текущем файле
            current_uid = str(row_data[1])
            if current_uid in seen_uids:
                invalid_rows.append(row_data)
                continue
            seen_uids.add(current_uid)

            is_valid = (
                validate_type(row_data[0]) and
                validate_uid(row_data[1]) and
                validate_value(row_data[2]) and
                validate_coordinate(row_data[3], 'latitude') and
                validate_coordinate(row_data[4], 'longitude') and
                validate_url(row_data[5])
            )

            if is_valid:
                try:
                    CollectibleItem.objects.create(
                        name=str(row_data[0]),
                        uid=current_uid,
                        value=int(float(str(row_data[2]))),
                        latitude=Decimal(str(row_data[3])),
                        longitude=Decimal(str(row_data[4])),
                        picture=str(row_data[5]).rstrip(';')  # Удаляем точку с запятой в конце
                    )
                except IntegrityError:
                    invalid_rows.append(row_data)  # Если UID уже существует в БД
            else:
                invalid_rows.append(row_data)

        return Response(invalid_rows, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
