from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import  viewsets
from openpyxl import load_workbook
from .models import CollectibleItem
from .serializers import CollectibleItemSerializer



@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=400)

    file = request.FILES['file']
    if not file.name.endswith('.xlsx'):
        return Response({"error": "Only XLSX files are supported"}, status=400)

    try:
        wb = load_workbook(filename=file)
        ws = wb.active
        results = {
            "total_rows": ws.max_row - 1,
            "created": 0,
            "errors": []
        }

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1:  # Пропускаем заголовок
                continue

            if not any(row):  # Пропускаем пустые строки
                continue

            try:
                # Правильное сопоставление столбцов (порядок как в Excel)
                data = {
                    'name': str(row[0]) if row[0] is not None else '',
                    'uid': str(row[1]) if row[1] is not None else '',
                    'value': row[2],  # 3-й столбец - Value
                    'latitude': row[3],  # 4-й столбец - Latitude
                    'longitude': row[4],  # 5-й столбец - Longitude
                    'picture': str(row[5]) if row[5] is not None else ''  # 6-й столбец - Picture
                }

                serializer = CollectibleItemSerializer(data=data)
                if serializer.is_valid():
                    try:
                        serializer.save()
                        results["created"] += 1
                    except Exception as e:
                        results["errors"].append({
                            "row": row_idx,
                            "error": f"Ошибка сохранения: {str(e)}",
                            "data": list(row)
                        })
                else:
                    results["errors"].append({
                        "row": row_idx,
                        "error": "Невалидные данные",
                        "details": serializer.errors,
                        "data": list(row)
                    })

            except Exception as e:
                results["errors"].append({
                    "row": row_idx,
                    "error": f"Ошибка обработки: {str(e)}",
                    "data": list(row)
                })

        return Response(results, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=400)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
