from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator

class RunStatusPydantic(str, Enum):
    INIT = "init"
    IN_PROGRESS = "in_progress"  # Исправлено на IN_PROGRESS (две S)
    FINISHED = "finished"



class RunBase(BaseModel):
    comment: str
    athlete: int
    status: RunStatusPydantic = RunStatusPydantic.INIT
    distance: Decimal = Field(default=Decimal('0.00'), ge=Decimal('0.00'))

    @field_validator('distance', mode='before')
    def parse_distance(cls, value):
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(round(value, 2)))
            if isinstance(value, Decimal):
                return value.quantize(Decimal('0.00'))
            return Decimal('0.00')
        except (ValueError, TypeError, InvalidOperation):
            return Decimal('0.00')


class RunCreate(RunBase):
    # Только поля, необходимые для создания
    # Можно оставить пустым или добавить дополнительные ограничения
    pass


class RunRead(RunBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )