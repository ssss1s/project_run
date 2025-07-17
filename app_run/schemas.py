from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class RunStatusPydantic(str, Enum):
    INIT = "init"
    IN_PROGRESS = "in_progress"  # Исправлено на IN_PROGRESS (две S)
    FINISHED = "finished"


class RunBase(BaseModel):
    comment: str
    athlete: int
    status: RunStatusPydantic = RunStatusPydantic.INIT
    distance: float = Field(default=0.0, ge=0)  # Заменили Decimal на float


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