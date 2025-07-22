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
        invalid_rows_data = []
        seen_uids = set()
        existing_uids = set(CollectibleItem.objects.values_list('uid', flat=True))

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1 or not any(row):  # Skip header and empty rows
                continue

            row_data = list(row)
            try:
                if len(row_data) < 6:
                    raise ValueError("Все поля должны быть заполнены (6 колонок)")

                # Prepare data dict
                item_data = {
                    'name': str(row_data[0]) if row_data[0] is not None else '',
                    'uid': str(row_data[1]) if row_data[1] is not None else '',
                    'value': str(row_data[2]) if row_data[2] is not None else '0',
                    'latitude': str(row_data[3]) if row_data[3] is not None else '',
                    'longitude': str(row_data[4]) if row_data[4] is not None else '',
                    'picture': str(row_data[5]).rstrip(';') if row_data[5] is not None else '',
                }

                # Check for duplicate UIDs in file
                if item_data['uid'] in seen_uids:
                    raise ValueError(f"UID {item_data['uid']} дублируется в файле")
                seen_uids.add(item_data['uid'])

                # Check if UID exists in DB
                if item_data['uid'] in existing_uids:
                    raise ValueError(f"UID {item_data['uid']} уже существует в базе")

                # Validate with serializer
                serializer = CollectibleItemSerializer(data=item_data)
                if not serializer.is_valid():
                    errors = "; ".join([f"{k}: {v[0]}" for k, v in serializer.errors.items()])
                    raise ValueError(errors)

                # Save valid data
                serializer.save()

            except Exception as e:
                invalid_rows_data.append(row_data)

        return Response(invalid_rows_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
