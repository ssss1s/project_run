from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class RunStatusPydantic(str, Enum):
    """Статусы пробежки (точно соответствуют Django-модели)"""
    INIT = "init"  # Создан
    IN_PROGRESS = "in_progress"  # В процессе (обратите внимание на одну 'S' - как в Django)
    FINISHED = "finished"  # Завершен


class RunBase(BaseModel):
    """Базовая модель пробежки (основные поля)"""
    comment: str  # Комментарий (аналог Django TextField)
    athlete: int  # ID пользователя (аналог ForeignKey на User)
    status: RunStatusPydantic = RunStatusPydantic.INIT  # Статус по умолчанию
    distance: Decimal = Field(default=Decimal('0.00'), ge=Decimal('0.00'))
    run_time_seconds: Decimal = Field(default=Decimal('0.00'), ge=Decimal('0.00'))

    @field_validator('distance', 'run_time_seconds', mode='before')
    def parse_decimal(cls, value):
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(round(value, 2)))
            if isinstance(value, Decimal):
                return value.quantize(Decimal('0.00'))
            return Decimal('0.00')
        except (ValueError, TypeError, InvalidOperation):
            return Decimal('0.00')


class RunRead(RunBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)  # Сохраняем точность
        }
    )