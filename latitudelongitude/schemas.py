from pydantic import BaseModel, Field, validator
from typing import Union
from django.db import models
from enum import Enum


class RunStatus(str, Enum):
    INIT = 'init'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class PositionCreate(BaseModel):
    run: int = Field(..., gt=0, description="ID забега")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    @validator('run')
    def validate_run_status(cls, run_id, values):
        from app_run.models import Run  # Ленивый импорт для избежания циклических импортов

        run = Run.objects.filter(id=run_id).first()
        if not run:
            raise ValueError("Забег не существует")
        if run.status != RunStatus.IN_PROGRESS:
            raise ValueError("Забег должен быть в статусе 'in_progress'")
        return run_id


class PositionResponse(BaseModel):
    id: int
    run_id: int = Field(..., alias="run")
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @validator('run_id', pre=True)
    def extract_run_id(cls, v):
        if hasattr(v, 'id'):
            return v.id
        return v