import uuid
from enum import Enum, StrEnum
from typing import TypeVar, Union, Any, TypeAlias

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from dplex.services.filters import (
    StringFilter,
    DateTimeFilter,
    NumberFilter,
    BooleanFilter,
    DateFilter,
    TimestampFilter,
    FloatFilter,
    DecimalFilter,
    BaseNumberFilter,
    TimeFilter,
    IntFilter,
    EnumFilter,
    UUIDFilter,
)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

KeyType = TypeVar("KeyType", int, str, uuid.UUID)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
FilterSchemaType = TypeVar("FilterSchemaType")

SortFieldSchemaType = TypeVar("SortFieldSchemaType")

# Generic type для поля сортировки
SortByType = TypeVar("SortByType", bound=StrEnum)

FilterType = (
    StringFilter
    | IntFilter
    | FloatFilter
    | DecimalFilter
    | BaseNumberFilter
    | DateTimeFilter
    | DateFilter
    | TimeFilter
    | TimestampFilter
    | BooleanFilter
    | EnumFilter
    | UUIDFilter
)


class NullMarker(Enum):
    """
    Специальные маркеры для операций с базой данных

    Attributes:
        NULL: Маркер для явной установки NULL в БД при обновлении.
              Отличается от None (не обновлять) и от обычного значения.

    Examples:
        >>> update = UserUpdate(email=NULL)
        >>> # email будет установлен в NULL в базе данных
    """

    NULL = "null"

    def __repr__(self) -> str:
        """Строковое представление маркера"""
        return self.name  # Вернёт "NULL"

    def __bool__(self) -> bool:
        """Логическое значение - всегда False для условий"""
        return False


# Синглтон
NULL = NullMarker.NULL
