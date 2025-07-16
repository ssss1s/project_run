from pydantic import BaseModel, Field, validator
from enum import Enum


class RunStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    NOT_STARTED = "not_started"


class PositionCreate(BaseModel):
    run_id: int = Field(..., alias="run", gt=0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    @validator("latitude", "longitude")
    def round_coordinates(cls, v):
        """Округляем координаты до 4 знаков после запятой."""
        return round(v, 4)


class PositionResponse(BaseModel):
    id: int
    run_id: int = Field(..., alias="run")
    latitude: float
    longitude: float

    class Config:
        orm_mode = True