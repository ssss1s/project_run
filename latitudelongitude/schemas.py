from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class RunStatus(str, Enum):
    INIT = 'init'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'

class PositionCreate(BaseModel):
    run: int = Field(..., gt=0, description="ID забега")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    distance: float = Field(..., ge=0.0)
    speed: str = Field(..., description="Скорость в м/с в виде строки")

    @validator('distance', pre=True)
    def convert_distance_to_km(cls, v):
        """Конвертирует метры в километры"""
        return round(float(v) / 1000, 5) if v is not None else 0.0

    @validator('speed', pre=True)
    def format_speed(cls, v):
        """Преобразует скорость в строку без округления"""
        if isinstance(v, (float, int)):
            return f"{v:.15f}".rstrip('0').rstrip('.') if '.' in f"{v}" else f"{v}"
        return str(v)

    @validator('run')
    def validate_run_status(cls, run_id, values):
        from app_run.models import Run  # Ленивый импорт

        run = Run.objects.filter(id=run_id).first()
        if not run:
            raise ValueError("Забег не существует")
        return run_id

class PositionResponse(BaseModel):
    id: int
    run_id: int = Field(..., alias="run")
    latitude: float
    longitude: float
    date_time: datetime
    distance: float
    speed: str = Field(..., description="Скорость в м/с в виде строки")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @validator('speed', pre=True)
    def format_speed_response(cls, v):
        """Обеспечивает строковое представление скорости"""
        if isinstance(v, (float, int)):
            # Убираем лишние нули после запятой
            return f"{v:.15f}".rstrip('0').rstrip('.') if '.' in f"{v}" else f"{v}"
        return str(v)

    @validator('run_id', pre=True)
    def extract_run_id(cls, v):
        if hasattr(v, 'id'):
            return v.id
        return v