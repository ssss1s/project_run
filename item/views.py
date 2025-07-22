import re
from decimal import InvalidOperation, Decimal
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

        # Получаем все существующие UID из базы один раз
        existing_uids = set(CollectibleItem.objects.values_list('uid', flat=True))
        valid_names = {'Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn'}

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):
                continue

            row_data = list(row)
            try:
                if len(row_data) < 6:
                    raise ValueError("Не все поля заполнены")

                # Базовые проверки перед созданием объекта
                name = str(row_data[0]) if row_data[0] is not None else ''
                uid = str(row_data[1]) if row_data[1] is not None else ''

                # 1. Проверка имени
                if name not in valid_names:
                    raise ValueError(f"Недопустимое имя предмета: {name}")

                # 2. Проверка UID
                if len(uid) != 8 or not re.fullmatch(r'^[a-f0-9]{8}$', uid.lower()):
                    raise ValueError("UID должен состоять из 8 hex-символов")

                # 3. Проверка на дубликаты в файле
                if uid in seen_uids:
                    raise ValueError(f"UID {uid} дублируется в файле")

                # 4. Проверка на существование в БД
                if uid in existing_uids:
                    raise ValueError(f"UID {uid} уже существует в базе")

                seen_uids.add(uid)

                # Создаем и валидируем объект
                item = CollectibleItem(
                    name=name,
                    uid=uid,
                    value=int(row_data[2]) if row_data[2] is not None else 0,
                    latitude=Decimal(str(row_data[3])) if row_data[3] is not None else Decimal('0'),
                    longitude=Decimal(str(row_data[4])) if row_data[4] is not None else Decimal('0'),
                    picture=str(row_data[5]).rstrip(';') if row_data[5] is not None else ''
                )

                # Полная валидация модели
                item.full_clean()
                item.save()

            except Exception as e:
                invalid_rows.append(row_data)

        return Response(invalid_rows, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
