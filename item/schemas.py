# item/schemas.py
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Literal
from decimal import Decimal, InvalidOperation
import re

# Определяем допустимые типы предметов
VALID_ITEM_TYPES = Literal['Coin', 'Flag', 'Sun', 'Key', 'Bottle', 'Horn']

class CollectibleItemCreate(BaseModel):
    name: VALID_ITEM_TYPES
    uid: str = Field(..., min_length=8, max_length=8)
    value: int = Field(..., gt=0)
    latitude: Decimal = Field(..., decimal_places=6)
    longitude: Decimal = Field(..., decimal_places=6)
    picture: HttpUrl

    @validator('uid')
    def validate_uid(cls, v):
        if not re.fullmatch(r'^[a-f0-9]{8}$', v.lower()):
            raise ValueError('UID должен состоять из 8 hex-символов')
        return v.lower()

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Широта должна быть между -90 и 90')
        return v.quantize(Decimal('0.000000'))

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Долгота должна быть между -180 и 180')
        return v.quantize(Decimal('0.000000'))

    @validator('latitude', 'longitude', pre=True)
    def parse_decimal(cls, v):
        try:
            if isinstance(v, Decimal):
                return v
            return Decimal(str(v).replace(',', '.'))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Invalid decimal value")