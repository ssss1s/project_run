from decimal import InvalidOperation, Decimal

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from openpyxl import load_workbook
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
        wb = load_workbook(file)
        ws = wb.active
        valid_items = []
        invalid_rows = []

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            # Пропускаем заголовок и пустые строки
            if row_idx == 1 or not any(row):
                continue

            try:
                # Подготавливаем данные для валидации
                data = {
                    'name': str(row[0]) if row[0] is not None else '',
                    'uid': str(row[1]),
                    'latitude': Decimal(str(row[2])) if row[2] is not None else None,
                    'longitude': Decimal(str(row[3])) if row[3] is not None else None,
                    'picture': str(row[4]) if row[4] is not None else '',
                    'value': int(row[5]) if row[5] is not None else None
                }

                # Валидация через сериализатор
                serializer = CollectibleItemSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    valid_items.append(serializer.data)
                else:
                    invalid_rows.append(list(row))

            except (ValueError, TypeError, InvalidOperation) as e:
                invalid_rows.append(list(row))

        return Response({
            "created": len(valid_items),
            "invalid_rows": invalid_rows
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer