import re
from decimal import InvalidOperation, Decimal
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from openpyxl import load_workbook
from rest_framework import status, viewsets
from .models import CollectibleItem
from .serializers import CollectibleItemSerializer



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

        # Заранее получаем все существующие UID и допустимые имена
        existing_uids = set(CollectibleItem.objects.values_list('uid', flat=True))
        valid_names = {'Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn'}

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):
                continue

            row_data = list(row)
            try:
                if len(row_data) < 6:
                    raise ValueError("Требуется 6 колонок данных")

                name = str(row_data[0]) if row_data[0] is not None else ''
                uid = str(row_data[1]) if row_data[1] is not None else ''

                # 1. Проверка имени
                if name not in valid_names:
                    raise ValueError(f"Недопустимое имя предмета: {name}")

                # 2. Проверка формата UID
                if len(uid) != 8 or not re.fullmatch(r'^[a-f0-9]{8}$', uid.lower()):
                    raise ValueError("Неверный формат UID")

                # 3. Проверка на дубликаты в файле
                if uid in seen_uids:
                    raise ValueError(f"UID {uid} дублируется в файле")

                # 4. Проверка на существование в БД
                if uid in existing_uids:
                    raise ValueError(f"UID {uid} уже существует в базе")

                seen_uids.add(uid)

                # 5. Проверка числовых значений
                try:
                    value = int(row_data[2]) if row_data[2] is not None else 0
                    if value <= 0:
                        raise ValueError("Значение должно быть положительным")
                except (TypeError, ValueError):
                    raise ValueError("Некорректное числовое значение")

                # 6. Проверка координат
                try:
                    lat = Decimal(str(row_data[3])) if row_data[3] is not None else None
                    lon = Decimal(str(row_data[4])) if row_data[4] is not None else None

                    if lat is None or lon is None:
                        raise ValueError("Координаты обязательны")

                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        raise ValueError("Координаты вне допустимого диапазона")
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError("Некорректные координаты")

                # 7. Проверка URL
                picture = str(row_data[5]).rstrip(';') if row_data[5] is not None else ''
                if not picture.startswith(('http://', 'https://')):
                    raise ValueError("Некорректный URL")

                # Если все проверки пройдены, создаем объект
                CollectibleItem.objects.create(
                    name=name,
                    uid=uid,
                    value=value,
                    latitude=lat,
                    longitude=lon,
                    picture=picture
                )

            except Exception as e:
                invalid_rows.append(row_data)

        return Response(invalid_rows, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
