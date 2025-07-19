from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, viewsets
from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
import re
from item.models import CollectibleItem
from item.serializers import CollectibleItemSerializer


def parse_value(value):
    """Convert value to integer"""
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        raise ValueError("Value must be a positive integer")


def parse_coordinate(value, coord_type):
    """Validate and convert coordinates"""
    try:
        coord = Decimal(str(value)).quantize(Decimal('0.000000'))
        if coord_type == 'latitude' and not -90 <= coord <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if coord_type == 'longitude' and not -180 <= coord <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return coord
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid {coord_type} value")


def validate_url(value):
    """Validate and clean URL"""
    url = str(value).strip()
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = f'https://{url}'
    if len(url) < 10:
        raise ValueError("URL is too short")
    return url


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
        results = []
        created_count = 0

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1:  # Skip header
                continue

            if not any(row):  # Skip empty rows
                continue

            row_data = list(row)
            item = {
                'row': row_idx,
                'data': row_data,
                'status': 'success',
                'errors': None
            }

            try:
                # Prepare data with proper validation
                data = {
                    'name': str(row[0])[:255] if row[0] is not None else '',
                    'uid': str(row[1])[:100],
                    'value': parse_value(row[2]),
                    'latitude': parse_coordinate(row[3], 'latitude'),
                    'longitude': parse_coordinate(row[4], 'longitude'),
                    'picture': validate_url(row[5])
                }

                # Add to results if validation passed
                results.append(item)
                created_count += 1

            except ValueError as e:
                item['status'] = 'error'
                item['errors'] = str(e)
                results.append(item)
            except Exception as e:
                item['status'] = 'error'
                item['errors'] = f"Processing error: {str(e)}"
                results.append(item)

        response_data = [
            {
                'total_rows': ws.max_row - 1,
                'created': created_count,
                'errors': [item for item in results if item['status'] == 'error']
            }
        ]

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response([{"error": str(e)}], status=status.HTTP_400_BAD_REQUEST)

class CollectibleItemViewSet(viewsets.ModelViewSet):
    queryset = CollectibleItem.objects.all()
    serializer_class = CollectibleItemSerializer
