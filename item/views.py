from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
from item.models import CollectibleItem
from rest_framework import status, viewsets
import re

from item.serializers import CollectibleItemSerializer


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

        # 1. Заранее загружаем ВСЕ необходимые данные из БД
        existing_items = CollectibleItem.objects.all()
        existing_uids = {item.uid for item in existing_items}
        valid_names = {'Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn'}
        seen_uids_in_file = set()

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):
                continue

            row_data = list(row)
            try:
                # 2. Базовый парсинг данных
                name = str(row_data[0]).strip() if row_data[0] is not None else ''
                uid = str(row_data[1]).strip().lower() if row_data[1] is not None else ''

                # 3. Жёсткая проверка имени
                if name not in valid_names:
                    raise ValueError(f"Invalid item name: {name}")

                # 4. Проверка формата UID
                if not re.fullmatch(r'^[a-f0-9]{8}$', uid):
                    raise ValueError("Invalid UID format")

                # 5. Проверка на дубликаты в файле
                if uid in seen_uids_in_file:
                    raise ValueError(f"Duplicate UID in file: {uid}")

                # 6. Проверка на существование в БД
                if uid in existing_uids:
                    raise ValueError(f"UID already exists: {uid}")

                seen_uids_in_file.add(uid)

                # 7. Проверка value
                try:
                    value = int(float(row_data[2])) if row_data[2] is not None else 0
                    if value <= 0:
                        raise ValueError("Value must be positive")
                except (ValueError, TypeError):
                    raise ValueError("Invalid value")

                # 8. Проверка координат
                try:
                    lat = Decimal(str(row_data[3]).replace(',', '.')) if row_data[3] is not None else None
                    lon = Decimal(str(row_data[4]).replace(',', '.')) if row_data[4] is not None else None
                    if lat is None or lon is None:
                        raise ValueError("Missing coordinates")
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        raise ValueError("Invalid coordinates range")
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError("Invalid coordinates")

                # 9. Проверка URL
                picture = str(row_data[5]).strip().rstrip(';') if row_data[5] is not None else ''
                if not picture.startswith(('http://', 'https://')):
                    raise ValueError("Invalid URL")

                # 10. Если все проверки пройдены - создаём объект
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
