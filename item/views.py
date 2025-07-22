from decimal import InvalidOperation
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from openpyxl import load_workbook
from django.db import IntegrityError
from rest_framework import status, viewsets
from pydantic import ValidationError
from .models import CollectibleItem
from .serializers import CollectibleItemSerializer
from .schemas import CollectibleItemCreate


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
        seen_uids = set()
        created_count = 0

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):  # Пропускаем заголовок и пустые строки
                continue

            try:
                row_data = list(row)
                if len(row_data) < 6:
                    raise ValueError("Не все поля заполнены (требуется 6 колонок)")

                # Подготовка данных с обработкой возможных None значений
                item_dict = {
                    'name': str(row_data[0]) if row_data[0] is not None else '',
                    'uid': str(row_data[1]) if row_data[1] is not None else '',
                    'value': str(row_data[2]) if row_data[2] is not None else '0',
                    'latitude': str(row_data[3]) if row_data[3] is not None else '',
                    'longitude': str(row_data[4]) if row_data[4] is not None else '',
                    'picture': str(row_data[5]).rstrip(';') if row_data[5] is not None else '',
                }

                # Проверка уникальности UID в текущем файле
                if item_dict['uid'] in seen_uids:
                    raise ValueError(f"UID {item_dict['uid']} дублируется в файле")
                seen_uids.add(item_dict['uid'])

                # Валидация с помощью Pydantic
                validated_data = CollectibleItemCreate.parse_obj(item_dict)

                # Создание объекта
                CollectibleItem.objects.create(**validated_data.dict())
                created_count += 1

            except (ValidationError, ValueError, IntegrityError, InvalidOperation) as e:
                error_msg = str(e)
                if isinstance(e, ValidationError):
                    error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])

                invalid_rows.append({
                    "row": row_idx,
                    "data": row_data,
                    "error": error_msg
                })

        return Response(invalid_rows, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Ошибка обработки файла: {str(e)}",
            "details": str(e.__class__.__name__)
        }, status=status.HTTP_400_BAD_REQUEST)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
