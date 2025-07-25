from datetime import datetime
from pydantic import BaseModel, Field, validator


class PositionCreate(BaseModel):
    run: int = Field(..., gt=0, description="ID забега")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    distance: float = Field(..., ge=0.0)
    speed: float = Field(..., ge=0.0)


class PositionFilter(BaseModel):
    run: int | None = Field(None, gt=0, description="ID забега для фильтрации")
    min_distance: float | None = Field(None, ge=0, description="Минимальная дистанция")
    max_distance: float | None = Field(None, ge=0, description="Максимальная дистанция")

    @validator('run')
    def validate_run_exists(cls, run_id):
        if run_id is not None:
            from app_run.models import Run
            if not Run.objects.filter(id=run_id).exists():
                raise ValueError("Забег с указанным ID не существует")
        return run_id

class PositionResponse(BaseModel):
    id: int
    run_id: int = Field(..., alias="run")
    latitude: float
    longitude: float
    date_time: datetime
    distance: float
    speed: float

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @validator('run_id', pre=True)
    def extract_run_id(cls, v):
        if hasattr(v, 'id'):
            return v.id
        return v