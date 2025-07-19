from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional
from decimal import Decimal

class CollectibleItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    uid: str = Field(..., max_length=100)
    latitude: Decimal = Field(..., decimal_places=6)
    longitude: Decimal = Field(..., decimal_places=6)
    picture: HttpUrl  # автоматическая валидация URL
    value: int

    @validator('latitude')
    def validate_latitude(cls, v):
        if not Decimal('-90') <= v <= Decimal('90'):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not Decimal('-180') <= v <= Decimal('180'):
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('value')
    def validate_value(cls, v):
        if v < 0:
            raise ValueError('Value must be positive')
        return v

    class Config:
        arbitrary_types_allowed = True  # для поддержки Decimal
        json_encoders = {
            Decimal: lambda v: str(v)  # сериализация Decimal в строку
        }


class CollectibleItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[Decimal] = Field(None, decimal_places=6)
    longitude: Optional[Decimal] = Field(None, decimal_places=6)
    picture: Optional[HttpUrl] = None
    value: Optional[int] = None

    # Можно добавить те же валидаторы, что и в Create


class CollectibleItemResponse(CollectibleItemCreate):
    id: int

    class Config:
        orm_mode = True


