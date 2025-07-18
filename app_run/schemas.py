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
    distance: Decimal = Field(default=Decimal('0.0'), ge=Decimal('0.0'))  # Дистанция (как FloatField в Django)

    @field_validator('distance', mode='before')
    def parse_distance(cls, value):
        """Валидатор для корректного преобразования дистанции"""
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(round(value, 1)))  # Округляем до 1 знака как FloatField
            if isinstance(value, Decimal):
                return value.quantize(Decimal('0.0'))  # Квантование до 0.0
            return Decimal('0.0')  # Значение по умолчанию при ошибках
        except (ValueError, TypeError, InvalidOperation):
            return Decimal('0.0')


class RunRead(RunBase):
    """Модель для чтения данных пробежки (включает ID и дату создания)"""
    id: int  # ID из БД
    created_at: datetime  # Дата создания (auto_now_add в Django)

    model_config = ConfigDict(
        from_attributes=True,  # Для работы с ORM (ранее known_as_orm_mode)
        json_encoders={
            datetime: lambda v: v.isoformat(),  # Сериализация даты в ISO-формат
            Decimal: lambda v: float(v)  # Десятичные числа -> float для JSON
        }
    )