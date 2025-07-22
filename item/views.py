from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
from item.models import CollectibleItem
from rest_framework import status, viewsets
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

        # 1. Получаем ВСЕ существующие данные из БД один раз
        existing_items = CollectibleItem.objects.all().values_list('uid', 'name')
        existing_uids = {uid.lower() for uid, name in existing_items}
        existing_name_uid_pairs = {(name, uid.lower()) for uid, name in existing_items}
        valid_names = {'Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn'}
        seen_uids_in_file = set()

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):
                continue

            row_data = list(row)
            try:
                # 2. Проверка наличия всех 6 полей
                if len(row_data) < 6:
                    raise ValueError("Требуется ровно 6 полей")

                # 3. Подготовка данных
                name = str(row_data[0]).strip()
                uid = str(row_data[1]).strip().lower()

                # 4. Жесткая проверка имени
                if name not in valid_names:
                    raise ValueError(f"Недопустимое имя: {name}")

                # 5. Проверка формата UID
                if not (len(uid) == 8 and all(c in '0123456789abcdef' for c in uid)):
                    raise ValueError("UID должен быть 8 hex-символов")

                # 6. Проверка на дубликаты в файле
                if uid in seen_uids_in_file:
                    raise ValueError(f"UID {uid} дублируется в файле")

                # 7. Двойная проверка на существование в БД
                if uid in existing_uids or (name, uid) in existing_name_uid_pairs:
                    raise ValueError(f"Объект {name} с UID {uid} уже существует")

                seen_uids_in_file.add(uid)

                # 8. Проверка value
                try:
                    value = int(float(str(row_data[2])))
                    if value <= 0:
                        raise ValueError("Значение должно быть > 0")
                except (ValueError, TypeError):
                    raise ValueError("Некорректное значение")

                # 9. Проверка координат
                try:
                    lat = Decimal(str(row_data[3]).replace(',', '.'))
                    lon = Decimal(str(row_data[4]).replace(',', '.'))
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        raise ValueError("Координаты вне диапазона")
                except (InvalidOperation, ValueError):
                    raise ValueError("Некорректные координаты")

                # 10. Проверка URL
                picture = str(row_data[5]).strip().rstrip(';')
                if not (picture.startswith(('http://', 'https://')) and ' ' not in picture):
                    raise ValueError("Некорректный URL")

                # Если все проверки пройдены - создаем объект
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
